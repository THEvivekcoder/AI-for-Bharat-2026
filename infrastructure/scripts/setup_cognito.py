#!/usr/bin/env python3
"""
AWS Cognito User Pool Setup Script for BharatSahayak

This script sets up AWS Cognito User Pool with:
- Phone number as username (primary identifier for rural users)
- OTP-based authentication flow
- Custom attributes: preferred_language, location
- Security configurations compliant with Requirements 11.1 and 11.2

Usage:
    python setup_cognito.py --environment dev
    python setup_cognito.py --environment prod --create-app-client
"""

import argparse
import json
import sys
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError


class CognitoUserPoolManager:
    """Manages AWS Cognito User Pool setup for BharatSahayak"""

    def __init__(self, environment: str, region: str = "ap-south-1"):
        self.environment = environment
        self.region = region
        self.pool_name = f"bharatsahayak-users-{environment}"
        self.cognito_client = boto3.client("cognito-idp", region_name=region)
        self.user_pool_id: Optional[str] = None
        self.app_client_id: Optional[str] = None

    def create_user_pool(self) -> str:
        """Create Cognito User Pool with phone number authentication"""
        print(f"Creating Cognito User Pool: {self.pool_name}")

        try:
            response = self.cognito_client.create_user_pool(
                PoolName=self.pool_name,
                # Phone number as username
                UsernameAttributes=["phone_number"],
                # Auto-verify phone numbers
                AutoVerifiedAttributes=["phone_number"],
                # User attributes
                Schema=[
                    {
                        "Name": "phone_number",
                        "AttributeDataType": "String",
                        "Required": True,
                        "Mutable": False,
                    },
                    {
                        "Name": "preferred_language",
                        "AttributeDataType": "String",
                        "Required": False,
                        "Mutable": True,
                        "StringAttributeConstraints": {"MinLength": "2", "MaxLength": "10"},
                    },
                    {
                        "Name": "location",
                        "AttributeDataType": "String",
                        "Required": False,
                        "Mutable": True,
                        "StringAttributeConstraints": {"MinLength": "1", "MaxLength": "100"},
                    },
                ],
                # Password policy (for future use if needed)
                Policies={
                    "PasswordPolicy": {
                        "MinimumLength": 8,
                        "RequireUppercase": False,
                        "RequireLowercase": False,
                        "RequireNumbers": True,
                        "RequireSymbols": False,
                        "TemporaryPasswordValidityDays": 7,
                    }
                },
                # MFA configuration - SMS for OTP
                MfaConfiguration="OPTIONAL",
                SmsConfiguration={
                    "SnsCallerArn": f"arn:aws:iam::{{account_id}}:role/bharatsahayak-cognito-sms-role-{self.environment}",
                    "ExternalId": f"bharatsahayak-{self.environment}",
                },
                # Account recovery
                AccountRecoverySetting={
                    "RecoveryMechanisms": [
                        {"Priority": 1, "Name": "verified_phone_number"}
                    ]
                },
                # User pool tags
                UserPoolTags={
                    "Environment": self.environment,
                    "Project": "BharatSahayak",
                    "ManagedBy": "setup_cognito.py",
                },
                # Email configuration (for future use)
                EmailConfiguration={
                    "EmailSendingAccount": "COGNITO_DEFAULT",
                },
                # Admin create user config
                AdminCreateUserConfig={
                    "AllowAdminCreateUserOnly": False,
                    "UnusedAccountValidityDays": 90,
                },
                # User attribute update settings
                UserAttributeUpdateSettings={
                    "AttributesRequireVerificationBeforeUpdate": ["phone_number"]
                },
            )

            self.user_pool_id = response["UserPool"]["Id"]
            print(f"✓ Created User Pool: {self.user_pool_id}")
            return self.user_pool_id

        except ClientError as e:
            if e.response["Error"]["Code"] == "UserPoolTaggingException":
                print("⚠ Warning: Could not tag user pool, but pool was created")
                return self.user_pool_id
            else:
                print(f"✗ Error creating user pool: {e}")
                sys.exit(1)

    def create_app_client(self, user_pool_id: str) -> str:
        """Create app client for the user pool"""
        print(f"\nCreating app client for user pool: {user_pool_id}")

        try:
            response = self.cognito_client.create_user_pool_client(
                UserPoolId=user_pool_id,
                ClientName=f"bharatsahayak-app-{self.environment}",
                # Token validity
                RefreshTokenValidity=30,  # 30 days
                AccessTokenValidity=60,  # 60 minutes
                IdTokenValidity=60,  # 60 minutes
                TokenValidityUnits={
                    "RefreshToken": "days",
                    "AccessToken": "minutes",
                    "IdToken": "minutes",
                },
                # Auth flows
                ExplicitAuthFlows=[
                    "ALLOW_CUSTOM_AUTH",
                    "ALLOW_USER_SRP_AUTH",
                    "ALLOW_REFRESH_TOKEN_AUTH",
                ],
                # Prevent user existence errors
                PreventUserExistenceErrors="ENABLED",
                # Enable token revocation
                EnableTokenRevocation=True,
                # Read and write attributes
                ReadAttributes=[
                    "phone_number",
                    "phone_number_verified",
                    "custom:preferred_language",
                    "custom:location",
                ],
                WriteAttributes=[
                    "phone_number",
                    "custom:preferred_language",
                    "custom:location",
                ],
            )

            self.app_client_id = response["UserPoolClient"]["ClientId"]
            print(f"✓ Created App Client: {self.app_client_id}")
            return self.app_client_id

        except ClientError as e:
            print(f"✗ Error creating app client: {e}")
            sys.exit(1)

    def configure_sms_mfa(self, user_pool_id: str) -> None:
        """Configure SMS MFA settings"""
        print(f"\nConfiguring SMS MFA for user pool: {user_pool_id}")

        try:
            self.cognito_client.set_user_pool_mfa_config(
                UserPoolId=user_pool_id,
                SmsMfaConfiguration={
                    "SmsAuthenticationMessage": "Your BharatSahayak verification code is {####}",
                    "SmsConfiguration": {
                        "SnsCallerArn": f"arn:aws:iam::{{account_id}}:role/bharatsahayak-cognito-sms-role-{self.environment}",
                        "ExternalId": f"bharatsahayak-{self.environment}",
                    },
                },
                MfaConfiguration="OPTIONAL",
            )

            print("✓ Configured SMS MFA")

        except ClientError as e:
            print(f"⚠ Warning: Could not configure SMS MFA: {e}")
            print("  Note: Ensure SNS SMS role exists with proper permissions")

    def get_user_pool_by_name(self) -> Optional[str]:
        """Find existing user pool by name"""
        try:
            response = self.cognito_client.list_user_pools(MaxResults=60)

            for pool in response.get("UserPools", []):
                if pool["Name"] == self.pool_name:
                    return pool["Id"]

            return None

        except ClientError as e:
            print(f"✗ Error listing user pools: {e}")
            return None

    def get_user_pool_info(self, user_pool_id: str) -> Dict:
        """Get detailed information about the user pool"""
        try:
            response = self.cognito_client.describe_user_pool(UserPoolId=user_pool_id)
            pool = response["UserPool"]

            return {
                "pool_id": pool["Id"],
                "pool_name": pool["Name"],
                "status": pool.get("Status", "Unknown"),
                "creation_date": str(pool.get("CreationDate", "")),
                "last_modified": str(pool.get("LastModifiedDate", "")),
                "mfa_configuration": pool.get("MfaConfiguration", "OFF"),
                "estimated_users": pool.get("EstimatedNumberOfUsers", 0),
                "username_attributes": pool.get("UsernameAttributes", []),
                "auto_verified_attributes": pool.get("AutoVerifiedAttributes", []),
            }

        except ClientError as e:
            print(f"✗ Error getting user pool info: {e}")
            return {}

    def list_app_clients(self, user_pool_id: str) -> List[Dict]:
        """List all app clients for the user pool"""
        try:
            response = self.cognito_client.list_user_pool_clients(
                UserPoolId=user_pool_id, MaxResults=60
            )

            clients = []
            for client in response.get("UserPoolClients", []):
                client_detail = self.cognito_client.describe_user_pool_client(
                    UserPoolId=user_pool_id, ClientId=client["ClientId"]
                )
                clients.append(
                    {
                        "client_id": client["ClientId"],
                        "client_name": client["ClientName"],
                        "creation_date": str(client_detail["UserPoolClient"].get("CreationDate", "")),
                    }
                )

            return clients

        except ClientError as e:
            print(f"✗ Error listing app clients: {e}")
            return []

    def verify_configuration(self, user_pool_id: str) -> None:
        """Verify that the user pool is properly configured"""
        print(f"\nVerifying configuration for user pool: {user_pool_id}")

        try:
            response = self.cognito_client.describe_user_pool(UserPoolId=user_pool_id)
            pool = response["UserPool"]

            # Check username attributes
            if "phone_number" in pool.get("UsernameAttributes", []):
                print("✓ Phone number configured as username")
            else:
                print("✗ Phone number NOT configured as username")

            # Check auto-verified attributes
            if "phone_number" in pool.get("AutoVerifiedAttributes", []):
                print("✓ Phone number auto-verification enabled")
            else:
                print("⚠ Phone number auto-verification NOT enabled")

            # Check custom attributes
            schema = pool.get("SchemaAttributes", [])
            custom_attrs = [
                attr["Name"]
                for attr in schema
                if attr.get("Name", "").startswith("custom:")
            ]

            if "custom:preferred_language" in custom_attrs:
                print("✓ Custom attribute 'preferred_language' configured")
            else:
                print("⚠ Custom attribute 'preferred_language' NOT found")

            if "custom:location" in custom_attrs:
                print("✓ Custom attribute 'location' configured")
            else:
                print("⚠ Custom attribute 'location' NOT found")

            # Check MFA configuration
            mfa_config = pool.get("MfaConfiguration", "OFF")
            print(f"✓ MFA Configuration: {mfa_config}")

        except ClientError as e:
            print(f"✗ Error verifying configuration: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Setup AWS Cognito User Pool for BharatSahayak"
    )
    parser.add_argument(
        "--environment",
        "-e",
        required=True,
        choices=["dev", "staging", "prod"],
        help="Deployment environment",
    )
    parser.add_argument(
        "--region",
        "-r",
        default="ap-south-1",
        help="AWS region (default: ap-south-1)",
    )
    parser.add_argument(
        "--create-app-client",
        action="store_true",
        help="Create app client for the user pool",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Display user pool information",
    )

    args = parser.parse_args()

    manager = CognitoUserPoolManager(args.environment, args.region)

    print("=" * 60)
    print("BharatSahayak Cognito User Pool Setup")
    print("=" * 60)

    # Check if user pool already exists
    existing_pool_id = manager.get_user_pool_by_name()

    if existing_pool_id:
        print(f"\n✓ User pool already exists: {existing_pool_id}")
        manager.user_pool_id = existing_pool_id
    else:
        # Create new user pool
        manager.user_pool_id = manager.create_user_pool()

    # Get and display user pool info
    if manager.user_pool_id:
        info = manager.get_user_pool_info(manager.user_pool_id)
        if info:
            print(f"\nUser Pool Information:")
            print(f"  Pool ID: {info['pool_id']}")
            print(f"  Pool Name: {info['pool_name']}")
            print(f"  Status: {info['status']}")
            print(f"  MFA Configuration: {info['mfa_configuration']}")
            print(f"  Estimated Users: {info['estimated_users']}")
            print(f"  Username Attributes: {', '.join(info['username_attributes'])}")

        # Verify configuration
        manager.verify_configuration(manager.user_pool_id)

        # Create app client if requested
        if args.create_app_client:
            print("\n" + "=" * 60)
            manager.app_client_id = manager.create_app_client(manager.user_pool_id)

        # List existing app clients
        clients = manager.list_app_clients(manager.user_pool_id)
        if clients:
            print(f"\nApp Clients ({len(clients)}):")
            for client in clients:
                print(f"  - {client['client_name']}: {client['client_id']}")

    print("\n" + "=" * 60)
    print("Setup complete!")
    print("\nNext Steps:")
    print("1. Create IAM role for Cognito SMS: bharatsahayak-cognito-sms-role")
    print("2. Attach AmazonCognitoSMSRole policy to the role")
    print("3. Update SNS SMS spending limit if needed")
    print("4. Create app client if not already created")
    print("5. Update application configuration with Pool ID and Client ID")
    print("=" * 60)


if __name__ == "__main__":
    main()
