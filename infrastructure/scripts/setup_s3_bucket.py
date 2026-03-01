#!/usr/bin/env python3
"""
S3 Bucket Setup Script for BharatSahayak Static Content

This script sets up the folder structure in the S3 bucket for:
- /schemes: Government scheme documents
- /documents: General documents and resources
- /cache: Cached data for offline functionality

Usage:
    python setup_s3_bucket.py --environment dev
    python setup_s3_bucket.py --environment prod --create-sample-structure
"""

import argparse
import json
import sys
from typing import Dict, List

import boto3
from botocore.exceptions import ClientError


class S3BucketManager:
    """Manages S3 bucket setup and folder structure for BharatSahayak"""

    def __init__(self, environment: str, region: str = "ap-south-1"):
        self.environment = environment
        self.region = region
        self.bucket_name = f"bharatsahayak-static-content-{environment}"
        self.s3_client = boto3.client("s3", region_name=region)

    def create_folder_structure(self) -> None:
        """Create the required folder structure in the S3 bucket"""
        folders = [
            "schemes/",
            "schemes/central/",
            "schemes/state/",
            "documents/",
            "documents/application-forms/",
            "documents/guidelines/",
            "cache/",
            "cache/schemes/",
            "cache/prices/",
            "cache/weather/",
        ]

        print(f"Creating folder structure in bucket: {self.bucket_name}")

        for folder in folders:
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=folder,
                    Body=b"",
                    ContentType="application/x-directory",
                )
                print(f"✓ Created folder: {folder}")
            except ClientError as e:
                print(f"✗ Error creating folder {folder}: {e}")
                sys.exit(1)

    def create_readme_files(self) -> None:
        """Create README files in each folder explaining their purpose"""
        readme_content = {
            "schemes/README.md": """# Schemes Folder

This folder contains government scheme documents and information.

## Structure:
- `central/`: Central government schemes
- `state/`: State-specific schemes

## File Naming Convention:
- Use kebab-case: `pradhan-mantri-kisan-samman-nidhi.pdf`
- Include scheme ID in metadata
- Keep filenames descriptive and searchable
""",
            "documents/README.md": """# Documents Folder

This folder contains general documents and resources.

## Structure:
- `application-forms/`: Downloadable application forms
- `guidelines/`: Guidelines and instructions

## File Types:
- PDF documents for offline access
- Images and infographics
- Multilingual versions (use language suffix: `-hi.pdf`, `-en.pdf`)
""",
            "cache/README.md": """# Cache Folder

This folder contains cached data for offline functionality.

## Structure:
- `schemes/`: Cached scheme information (JSON)
- `prices/`: Cached mandi prices (JSON)
- `weather/`: Cached weather data (JSON)

## Lifecycle:
- Files older than 90 days are automatically deleted
- Files older than 30 days are moved to Infrequent Access storage
""",
        }

        print("\nCreating README files...")

        for key, content in readme_content.items():
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=content.encode("utf-8"),
                    ContentType="text/markdown",
                )
                print(f"✓ Created: {key}")
            except ClientError as e:
                print(f"✗ Error creating {key}: {e}")

    def upload_sample_scheme(self) -> None:
        """Upload a sample scheme document for testing"""
        sample_scheme = {
            "scheme_id": "pm-kisan-001",
            "name": "Pradhan Mantri Kisan Samman Nidhi",
            "name_hi": "प्रधानमंत्री किसान सम्मान निधि",
            "category": "agriculture",
            "description": "Income support to all farmer families",
            "benefits": ["₹6000 per year in three installments"],
            "eligibility": {
                "occupation": ["farmer"],
                "land_holding": "Any size",
            },
            "documents_required": [
                "Aadhaar Card",
                "Bank Account Details",
                "Land Ownership Documents",
            ],
            "application_process": [
                "Visit PM-KISAN portal",
                "Register with Aadhaar",
                "Fill application form",
                "Submit land records",
            ],
            "last_updated": "2024-01-15",
        }

        key = "schemes/central/pm-kisan-sample.json"

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(sample_scheme, indent=2, ensure_ascii=False).encode(
                    "utf-8"
                ),
                ContentType="application/json",
                Metadata={
                    "scheme-id": "pm-kisan-001",
                    "category": "agriculture",
                    "language": "en",
                },
            )
            print(f"\n✓ Uploaded sample scheme: {key}")
        except ClientError as e:
            print(f"✗ Error uploading sample scheme: {e}")

    def verify_bucket_policy(self) -> None:
        """Verify that the bucket policy allows public read access"""
        print("\nVerifying bucket policy...")

        try:
            policy = self.s3_client.get_bucket_policy(Bucket=self.bucket_name)
            policy_doc = json.loads(policy["Policy"])

            # Check for public read access
            has_public_read = False
            for statement in policy_doc.get("Statement", []):
                if (
                    statement.get("Effect") == "Allow"
                    and statement.get("Principal") == "*"
                    and "s3:GetObject" in statement.get("Action", [])
                ):
                    has_public_read = True
                    break

            if has_public_read:
                print("✓ Bucket policy allows public read access to scheme documents")
            else:
                print("⚠ Warning: Bucket policy may not allow public read access")

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
                print("⚠ Warning: No bucket policy found. Deploy the CloudFormation stack first.")
            else:
                print(f"✗ Error checking bucket policy: {e}")

    def list_bucket_contents(self) -> None:
        """List the contents of the bucket"""
        print(f"\nListing contents of bucket: {self.bucket_name}")

        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)

            if "Contents" not in response:
                print("Bucket is empty")
                return

            print(f"\nFound {len(response['Contents'])} objects:")
            for obj in response["Contents"]:
                size = obj["Size"]
                size_str = f"{size} bytes" if size > 0 else "folder"
                print(f"  - {obj['Key']} ({size_str})")

        except ClientError as e:
            print(f"✗ Error listing bucket contents: {e}")

    def get_bucket_info(self) -> Dict:
        """Get information about the bucket"""
        try:
            # Get bucket location
            location = self.s3_client.get_bucket_location(Bucket=self.bucket_name)
            region = location["LocationConstraint"] or "us-east-1"

            # Get bucket versioning
            versioning = self.s3_client.get_bucket_versioning(Bucket=self.bucket_name)

            # Get bucket CORS
            try:
                cors = self.s3_client.get_bucket_cors(Bucket=self.bucket_name)
                has_cors = True
            except ClientError:
                has_cors = False

            return {
                "bucket_name": self.bucket_name,
                "region": region,
                "versioning": versioning.get("Status", "Disabled"),
                "cors_enabled": has_cors,
                "url": f"https://{self.bucket_name}.s3.{region}.amazonaws.com",
            }

        except ClientError as e:
            print(f"✗ Error getting bucket info: {e}")
            return {}


def main():
    parser = argparse.ArgumentParser(
        description="Setup S3 bucket for BharatSahayak static content"
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
        "--create-sample-structure",
        action="store_true",
        help="Create sample folder structure and files",
    )
    parser.add_argument(
        "--list-contents",
        action="store_true",
        help="List bucket contents",
    )

    args = parser.parse_args()

    manager = S3BucketManager(args.environment, args.region)

    # Get bucket info
    print("=" * 60)
    print("BharatSahayak S3 Bucket Setup")
    print("=" * 60)

    info = manager.get_bucket_info()
    if info:
        print(f"\nBucket Name: {info['bucket_name']}")
        print(f"Region: {info['region']}")
        print(f"Versioning: {info['versioning']}")
        print(f"CORS Enabled: {info['cors_enabled']}")
        print(f"URL: {info['url']}")

    # Create folder structure
    if args.create_sample_structure:
        print("\n" + "=" * 60)
        manager.create_folder_structure()
        manager.create_readme_files()
        manager.upload_sample_scheme()

    # Verify bucket policy
    manager.verify_bucket_policy()

    # List contents
    if args.list_contents or args.create_sample_structure:
        manager.list_bucket_contents()

    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
