#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
import time
from datetime import datetime, timedelta


class AWSCredentialsMixin:
    """
    Mixin class that provides elegant AWS credential management with automatic refresh
    for cross-account role assumption.
    """

    def __init__(
        self, profile_name=None, region_name=None, role_arn=None, external_id=None
    ):
        """Initialize AWS credentials management.

        Args:
            profile_name: Optional AWS profile name to use for credentials
            region_name: Optional AWS region name to use for API calls
            role_arn: Optional ARN of the role to assume in another AWS account
            external_id: Optional external ID for cross-account role assumption
        """
        self.profile_name = profile_name
        self.region_name = region_name
        self.role_arn = role_arn
        self.external_id = external_id

        # Credential management state
        self._assumed_session = None
        self._credentials_expiry = None

        # Buffer time before credential expiry to trigger refresh (5 minutes)
        self._refresh_buffer = timedelta(minutes=5)

    def get_session(self) -> boto3.Session:
        """Get a boto3 session with fresh credentials.

        Returns:
            boto3.Session: A session with valid credentials
        """
        if self.role_arn:
            return self._get_cross_account_session()
        else:
            return boto3.Session(
                profile_name=self.profile_name, region_name=self.region_name
            )

    def get_client(self, service_name: str, **kwargs) -> object:
        """Get an AWS service client with fresh credentials.

        Args:
            service_name: AWS service name (e.g., 'logs', 'cloudwatch')
            **kwargs: Additional arguments to pass to the client

        Returns:
            AWS service client with fresh credentials
        """
        session = self.get_session()
        return session.client(service_name, **kwargs)

    def _get_cross_account_session(self) -> boto3.Session:
        """Get or create a cross-account session with credential refresh logic."""
        if self._is_session_valid():
            return self._assumed_session

        return self._create_cross_account_session()

    def _is_session_valid(self) -> bool:
        """Check if the current session is valid and not expired."""
        if not self._assumed_session or not self._credentials_expiry:
            return False

        current_time = datetime.utcnow()
        return current_time < self._credentials_expiry - self._refresh_buffer

    def _create_cross_account_session(self) -> boto3.Session:
        """Perform the actual role assumption and session creation."""
        # Create source session
        source_session = boto3.Session(
            profile_name=self.profile_name, region_name=self.region_name
        )

        # Assume the role
        sts_client = source_session.client("sts")
        assume_role_params = {
            "RoleArn": self.role_arn,
            "RoleSessionName": f"CloudWatchLogs-{int(time.time())}",
        }

        if self.external_id:
            assume_role_params["ExternalId"] = self.external_id

        try:
            response = sts_client.assume_role(**assume_role_params)
        except Exception as e:
            raise Exception(f"Failed to assume role {self.role_arn}: {str(e)}")

        # Store expiry time
        self._credentials_expiry = response["Credentials"]["Expiration"]

        # Create and store the new session
        self._assumed_session = boto3.Session(
            aws_access_key_id=response["Credentials"]["AccessKeyId"],
            aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
            aws_session_token=response["Credentials"]["SessionToken"],
            region_name=self.region_name,
        )

        return self._assumed_session
