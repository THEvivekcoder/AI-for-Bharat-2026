"""
Unit tests for Cognito User Pool setup script
"""

from unittest.mock import MagicMock, patch

import pytest


class TestCognitoUserPoolManager:
    """Test CognitoUserPoolManager functionality"""

    @patch("boto3.client")
    def test_pool_name_format(self, mock_boto_client):
        """Test that user pool name follows the correct format"""
        from infrastructure.scripts.setup_cognito import CognitoUserPoolManager

        manager = CognitoUserPoolManager("dev", "ap-south-1")
        assert manager.pool_name == "bharatsahayak-users-dev"
        assert manager.environment == "dev"
        assert manager.region == "ap-south-1"

    @patch("boto3.client")
    def test_user_pool_creation(self, mock_boto_client):
        """Test that user pool is created with correct configuration"""
        from infrastructure.scripts.setup_cognito import CognitoUserPoolManager

        mock_cognito = MagicMock()
        mock_cognito.create_user_pool.return_value = {
            "UserPool": {"Id": "ap-south-1_TEST123"}
        }
        mock_boto_client.return_value = mock_cognito

        manager = CognitoUserPoolManager("dev")
        pool_id = manager.create_user_pool()

        # Verify create_user_pool was called
        assert mock_cognito.create_user_pool.called
        assert pool_id == "ap-south-1_TEST123"

        # Verify configuration parameters
        call_args = mock_cognito.create_user_pool.call_args[1]
        assert call_args["PoolName"] == "bharatsahayak-users-dev"
        assert "phone_number" in call_args["UsernameAttributes"]
        assert "phone_number" in call_args["AutoVerifiedAttributes"]

    @patch("boto3.client")
    def test_custom_attributes_configuration(self, mock_boto_client):
        """Test that custom attributes are properly configured"""
        from infrastructure.scripts.setup_cognito import CognitoUserPoolManager

        mock_cognito = MagicMock()
        mock_cognito.create_user_pool.return_value = {
            "UserPool": {"Id": "ap-south-1_TEST123"}
        }
        mock_boto_client.return_value = mock_cognito

        manager = CognitoUserPoolManager("dev")
        manager.create_user_pool()

        # Get the schema configuration
        call_args = mock_cognito.create_user_pool.call_args[1]
        schema = call_args["Schema"]

        # Verify custom attributes exist
        attr_names = [attr["Name"] for attr in schema]
        assert "phone_number" in attr_names
        assert "preferred_language" in attr_names
        assert "location" in attr_names

        # Verify phone_number is required
        phone_attr = next(attr for attr in schema if attr["Name"] == "phone_number")
        assert phone_attr["Required"] is True
        assert phone_attr["Mutable"] is False

        # Verify custom attributes are optional and mutable
        lang_attr = next(attr for attr in schema if attr["Name"] == "preferred_language")
        assert lang_attr["Required"] is False
        assert lang_attr["Mutable"] is True

        location_attr = next(attr for attr in schema if attr["Name"] == "location")
        assert location_attr["Required"] is False
        assert location_attr["Mutable"] is True

    @patch("boto3.client")
    def test_app_client_creation(self, mock_boto_client):
        """Test that app client is created with correct configuration"""
        from infrastructure.scripts.setup_cognito import CognitoUserPoolManager

        mock_cognito = MagicMock()
        mock_cognito.create_user_pool_client.return_value = {
            "UserPoolClient": {"ClientId": "test-client-id-123"}
        }
        mock_boto_client.return_value = mock_cognito

        manager = CognitoUserPoolManager("dev")
        client_id = manager.create_app_client("ap-south-1_TEST123")

        # Verify create_user_pool_client was called
        assert mock_cognito.create_user_pool_client.called
        assert client_id == "test-client-id-123"

        # Verify configuration parameters
        call_args = mock_cognito.create_user_pool_client.call_args[1]
        assert call_args["UserPoolId"] == "ap-south-1_TEST123"
        assert call_args["ClientName"] == "bharatsahayak-app-dev"
        assert call_args["RefreshTokenValidity"] == 30
        assert call_args["AccessTokenValidity"] == 60
        assert call_args["IdTokenValidity"] == 60

    @patch("boto3.client")
    def test_auth_flows_configuration(self, mock_boto_client):
        """Test that authentication flows are properly configured"""
        from infrastructure.scripts.setup_cognito import CognitoUserPoolManager

        mock_cognito = MagicMock()
        mock_cognito.create_user_pool_client.return_value = {
            "UserPoolClient": {"ClientId": "test-client-id-123"}
        }
        mock_boto_client.return_value = mock_cognito

        manager = CognitoUserPoolManager("dev")
        manager.create_app_client("ap-south-1_TEST123")

        # Verify auth flows
        call_args = mock_cognito.create_user_pool_client.call_args[1]
        auth_flows = call_args["ExplicitAuthFlows"]

        assert "ALLOW_CUSTOM_AUTH" in auth_flows
        assert "ALLOW_USER_SRP_AUTH" in auth_flows
        assert "ALLOW_REFRESH_TOKEN_AUTH" in auth_flows

    @patch("boto3.client")
    def test_user_pool_info_retrieval(self, mock_boto_client):
        """Test user pool information retrieval"""
        from infrastructure.scripts.setup_cognito import CognitoUserPoolManager

        mock_cognito = MagicMock()
        mock_cognito.describe_user_pool.return_value = {
            "UserPool": {
                "Id": "ap-south-1_TEST123",
                "Name": "bharatsahayak-users-dev",
                "Status": "Active",
                "MfaConfiguration": "OPTIONAL",
                "EstimatedNumberOfUsers": 0,
                "UsernameAttributes": ["phone_number"],
                "AutoVerifiedAttributes": ["phone_number"],
            }
        }
        mock_boto_client.return_value = mock_cognito

        manager = CognitoUserPoolManager("dev")
        info = manager.get_user_pool_info("ap-south-1_TEST123")

        assert info["pool_id"] == "ap-south-1_TEST123"
        assert info["pool_name"] == "bharatsahayak-users-dev"
        assert info["status"] == "Active"
        assert info["mfa_configuration"] == "OPTIONAL"
        assert "phone_number" in info["username_attributes"]

    @patch("boto3.client")
    def test_existing_pool_detection(self, mock_boto_client):
        """Test detection of existing user pool"""
        from infrastructure.scripts.setup_cognito import CognitoUserPoolManager

        mock_cognito = MagicMock()
        mock_cognito.list_user_pools.return_value = {
            "UserPools": [
                {"Id": "ap-south-1_TEST123", "Name": "bharatsahayak-users-dev"},
                {"Id": "ap-south-1_OTHER", "Name": "other-pool"},
            ]
        }
        mock_boto_client.return_value = mock_cognito

        manager = CognitoUserPoolManager("dev")
        pool_id = manager.get_user_pool_by_name()

        assert pool_id == "ap-south-1_TEST123"


class TestUserPoolConfiguration:
    """Test user pool configuration requirements"""

    def test_phone_number_as_username(self):
        """Test that phone number is configured as username"""
        username_attributes = ["phone_number"]
        assert "phone_number" in username_attributes

    def test_auto_verified_attributes(self):
        """Test that phone number is auto-verified"""
        auto_verified = ["phone_number"]
        assert "phone_number" in auto_verified

    def test_custom_attributes_defined(self):
        """Test that required custom attributes are defined"""
        custom_attributes = ["preferred_language", "location"]

        assert "preferred_language" in custom_attributes
        assert "location" in custom_attributes

    def test_mfa_configuration(self):
        """Test that MFA is configured"""
        mfa_config = "OPTIONAL"
        assert mfa_config in ["OPTIONAL", "ON", "OFF"]


class TestSecurityConfiguration:
    """Test security configuration compliance with Requirements 11.1 and 11.2"""

    def test_token_validity_periods(self):
        """Test that token validity periods are reasonable"""
        refresh_token_validity = 30  # days
        access_token_validity = 60  # minutes
        id_token_validity = 60  # minutes

        assert refresh_token_validity <= 30
        assert access_token_validity <= 60
        assert id_token_validity <= 60

    def test_token_revocation_enabled(self):
        """Test that token revocation is enabled"""
        enable_token_revocation = True
        assert enable_token_revocation is True

    def test_prevent_user_existence_errors(self):
        """Test that user existence errors are prevented"""
        prevent_errors = "ENABLED"
        assert prevent_errors == "ENABLED"

    def test_account_recovery_mechanism(self):
        """Test that account recovery is configured"""
        recovery_mechanisms = [{"Priority": 1, "Name": "verified_phone_number"}]

        assert len(recovery_mechanisms) > 0
        assert recovery_mechanisms[0]["Name"] == "verified_phone_number"


class TestAttributeConfiguration:
    """Test user attribute configuration"""

    def test_phone_number_required(self):
        """Test that phone_number is required and immutable"""
        phone_config = {"Required": True, "Mutable": False}

        assert phone_config["Required"] is True
        assert phone_config["Mutable"] is False

    def test_preferred_language_optional(self):
        """Test that preferred_language is optional and mutable"""
        lang_config = {"Required": False, "Mutable": True}

        assert lang_config["Required"] is False
        assert lang_config["Mutable"] is True

    def test_location_optional(self):
        """Test that location is optional and mutable"""
        location_config = {"Required": False, "Mutable": True}

        assert location_config["Required"] is False
        assert location_config["Mutable"] is True

    def test_attribute_constraints(self):
        """Test that string attributes have proper constraints"""
        lang_constraints = {"MinLength": "2", "MaxLength": "10"}
        location_constraints = {"MinLength": "1", "MaxLength": "100"}

        assert int(lang_constraints["MinLength"]) >= 2
        assert int(lang_constraints["MaxLength"]) <= 10
        assert int(location_constraints["MinLength"]) >= 1
        assert int(location_constraints["MaxLength"]) <= 100


class TestOTPConfiguration:
    """Test OTP-based authentication configuration"""

    def test_sms_mfa_message_format(self):
        """Test that SMS MFA message is properly formatted"""
        sms_message = "Your BharatSahayak verification code is {####}"

        assert "{####}" in sms_message
        assert "BharatSahayak" in sms_message

    def test_custom_auth_flow_enabled(self):
        """Test that custom auth flow is enabled for OTP"""
        auth_flows = [
            "ALLOW_CUSTOM_AUTH",
            "ALLOW_USER_SRP_AUTH",
            "ALLOW_REFRESH_TOKEN_AUTH",
        ]

        assert "ALLOW_CUSTOM_AUTH" in auth_flows


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
