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
   
   If you're seeing errors like `An error occurred (AccessDenied) when calling the DescribeLogGroups operation: Access denied`, make sure to add your credentials in this format:
   ```ini
   [default]
   aws_access_key_id = your-access-key
   aws_secret_access_key = your-secret-key
   
   # For temporary credentials, add the session token
   [temp-profile]
   aws_access_key_id = your-temp-access-key
   aws_secret_access_key = your-temp-secret-key
   aws_session_token = your-session-token
   ```

   Check out the [troubleshooting guide](./troubleshooting.md) for more information.

3. **AWS config file** (`~/.aws/config`):
   ```ini
   [default]
   region = us-east-1
   ```

You can set up your AWS credentials using the AWS CLI:

```bash
aws configure
```

## Using a Specific AWS Profile or Region

1. **Server Start-up**

   If you have multiple AWS profiles or want to specify a region, use:
   
   ```bash
   uvx --from git+https://github.com/awslabs/Log-Analyzer-with-MCP cw-mcp-server --profile your-profile-name --region us-west-2
   ```

2. **Per-Call Override**

   Override the profile or region on individual AI prompts or tool calls:
   
   > Example: Get a list of CloudWatch log groups using the "dev-account" profile in "eu-central-1" region.

   Once you set a profile or region, the LLM keeps using it for follow-ups. Only specify a new profile or region when you need to switch accounts or regions.

This is useful when you need to access CloudWatch logs in different AWS accounts or regions.

## 🛡️ Required Permissions

The MCP server requires permissions to access CloudWatch Logs. At minimum, ensure your IAM user or role has the following policies:
- `CloudWatchLogsReadOnlyAccess`
