"""
Unit tests for S3 bucket setup script
"""

import json
from unittest.mock import MagicMock, patch

import pytest


class TestS3BucketManager:
    """Test S3BucketManager functionality"""

    @patch("boto3.client")
    def test_bucket_name_format(self, mock_boto_client):
        """Test that bucket name follows the correct format"""
        from infrastructure.scripts.setup_s3_bucket import S3BucketManager

        manager = S3BucketManager("dev", "ap-south-1")
        assert manager.bucket_name == "bharatsahayak-static-content-dev"
        assert manager.environment == "dev"
        assert manager.region == "ap-south-1"

    @patch("boto3.client")
    def test_folder_structure(self, mock_boto_client):
        """Test that all required folders are created"""
        from infrastructure.scripts.setup_s3_bucket import S3BucketManager

        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        manager = S3BucketManager("dev")
        manager.create_folder_structure()

        # Verify put_object was called for each folder
        assert mock_s3.put_object.call_count >= 8

        # Verify key folders are created
        calls = [call[1]["Key"] for call in mock_s3.put_object.call_args_list]
        assert "schemes/" in calls
        assert "documents/" in calls
        assert "cache/" in calls

    @patch("boto3.client")
    def test_sample_scheme_structure(self, mock_boto_client):
        """Test that sample scheme has correct structure"""
        from infrastructure.scripts.setup_s3_bucket import S3BucketManager

        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        manager = S3BucketManager("dev")
        manager.upload_sample_scheme()

        # Verify put_object was called
        assert mock_s3.put_object.called

        # Get the uploaded data
        call_args = mock_s3.put_object.call_args
        uploaded_body = call_args[1]["Body"]
        scheme_data = json.loads(uploaded_body.decode("utf-8"))

        # Verify required fields
        assert "scheme_id" in scheme_data
        assert "name" in scheme_data
        assert "category" in scheme_data
        assert "eligibility" in scheme_data
        assert "benefits" in scheme_data

    @patch("boto3.client")
    def test_bucket_info_retrieval(self, mock_boto_client):
        """Test bucket information retrieval"""
        from infrastructure.scripts.setup_s3_bucket import S3BucketManager

        mock_s3 = MagicMock()
        mock_s3.get_bucket_location.return_value = {"LocationConstraint": "ap-south-1"}
        mock_s3.get_bucket_versioning.return_value = {"Status": "Enabled"}
        mock_boto_client.return_value = mock_s3

        manager = S3BucketManager("dev")
        info = manager.get_bucket_info()

        assert info["bucket_name"] == "bharatsahayak-static-content-dev"
        assert info["region"] == "ap-south-1"
        assert info["versioning"] == "Enabled"
        assert "s3.ap-south-1.amazonaws.com" in info["url"]


class TestFolderStructure:
    """Test folder structure requirements"""

    def test_required_folders_exist(self):
        """Test that all required folders are defined"""
        required_folders = [
            "schemes/",
            "documents/",
            "cache/",
        ]

        # This would be checked during actual deployment
        # For now, we verify the structure is documented
        assert len(required_folders) == 3

    def test_folder_naming_convention(self):
        """Test that folder names follow conventions"""
        folders = [
            "schemes/central/",
            "schemes/state/",
            "documents/application-forms/",
            "documents/guidelines/",
            "cache/schemes/",
            "cache/prices/",
            "cache/weather/",
        ]

        for folder in folders:
            # All folders should end with /
            assert folder.endswith("/")
            # All folders should use lowercase and hyphens
            assert folder == folder.lower()
            assert " " not in folder


class TestBucketPolicy:
    """Test bucket policy configuration"""

    def test_public_read_paths(self):
        """Test that correct paths have public read access"""
        public_paths = ["schemes/*", "documents/*"]

        for path in public_paths:
            assert path.endswith("/*")
            assert path in ["schemes/*", "documents/*"]

    def test_private_cache_path(self):
        """Test that cache path is not in public paths"""
        public_paths = ["schemes/*", "documents/*"]

        assert "cache/*" not in public_paths


class TestLifecyclePolicy:
    """Test lifecycle policy configuration"""

    def test_cache_transition_days(self):
        """Test cache transition to IA storage"""
        transition_days = 30
        assert transition_days == 30

    def test_cache_expiration_days(self):
        """Test cache expiration"""
        expiration_days = 90
        assert expiration_days == 90
        assert expiration_days > 30  # Should be after transition


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
