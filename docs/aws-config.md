# 🔐 AWS Configuration Guide

For the MCP server to access your AWS CloudWatch Logs, you need to configure AWS credentials, which you can learn how to do [here](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html). The server uses boto3's credential resolution chain, which checks several locations in the following order:

1. **Environment variables**:
   ```bash
   export AWS_ACCESS_KEY_ID="your-access-key"
   export AWS_SECRET_ACCESS_KEY="your-secret-key"
   export AWS_REGION="us-east-1"
   ```

2. **Shared credential file** (`~/.aws/credentials`):
   ```ini
   [default]
   aws_access_key_id = your-access-key
   aws_secret_access_key = your-secret-key
   ```

3. **AWS config file** (`~/.aws/config`):
   ```ini
   [default]
   region = us-east-1
   ```

You can set up your AWS credentials using the AWS CLI:

```bash
aws configure
```

## Using a Specific AWS Profile

If you have multiple AWS profiles configured, you can specify which profile to use when starting the MCP server:

```bash
python src/cw-mcp-server/server.py --profile your-profile-name
```

This is useful when you need to access CloudWatch logs in different AWS accounts or regions.

## 🛡️ Required Permissions

The MCP server requires permissions to access CloudWatch Logs. At minimum, ensure your IAM user or role has the following policies:
- `CloudWatchLogsReadOnlyAccess` 