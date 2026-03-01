#!/usr/bin/env python3
"""
Script to create DynamoDB tables for BharatSahayak
Can be used for local development with DynamoDB Local or AWS deployment
"""

import boto3
import sys
from botocore.exceptions import ClientError


def create_users_table(dynamodb, table_name):
    """Create Users table with partition key: user_id"""
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'phone_number', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'phone-number-index',
                    'KeySchema': [
                        {'AttributeName': 'phone_number', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✓ Created table: {table_name}")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ Table already exists: {table_name}")
        else:
            print(f"✗ Error creating {table_name}: {e}")
            raise


def create_schemes_table(dynamodb, table_name):
    """Create Schemes table with partition key: scheme_id, GSI on category"""
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'scheme_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'scheme_id', 'AttributeType': 'S'},
                {'AttributeName': 'category', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'category-index',
                    'KeySchema': [
                        {'AttributeName': 'category', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✓ Created table: {table_name}")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ Table already exists: {table_name}")
        else:
            print(f"✗ Error creating {table_name}: {e}")
            raise


def create_user_profiles_table(dynamodb, table_name):
    """Create UserProfiles table with partition key: user_id"""
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✓ Created table: {table_name}")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ Table already exists: {table_name}")
        else:
            print(f"✗ Error creating {table_name}: {e}")
            raise


def create_interactions_table(dynamodb, table_name):
    """Create Interactions table with partition key: user_id, sort key: timestamp"""
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✓ Created table: {table_name}")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ Table already exists: {table_name}")
        else:
            print(f"✗ Error creating {table_name}: {e}")
            raise


def create_farm_profiles_table(dynamodb, table_name):
    """Create FarmProfiles table with partition key: user_id"""
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✓ Created table: {table_name}")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ Table already exists: {table_name}")
        else:
            print(f"✗ Error creating {table_name}: {e}")
            raise


def main():
    """Create all DynamoDB tables"""
    # Parse command line arguments
    environment = sys.argv[1] if len(sys.argv) > 1 else 'dev'
    endpoint_url = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Configure DynamoDB client
    config = {'region_name': 'ap-south-1'}
    if endpoint_url:
        config['endpoint_url'] = endpoint_url
        print(f"Using DynamoDB Local at {endpoint_url}")
    else:
        print(f"Using AWS DynamoDB in region {config['region_name']}")
    
    dynamodb = boto3.resource('dynamodb', **config)
    
    # Table names with environment prefix
    tables = {
        'users': f'bharatsahayak-users-{environment}',
        'schemes': f'bharatsahayak-schemes-{environment}',
        'user_profiles': f'bharatsahayak-user-profiles-{environment}',
        'interactions': f'bharatsahayak-interactions-{environment}',
        'farm_profiles': f'bharatsahayak-farm-profiles-{environment}'
    }
    
    print(f"\nCreating DynamoDB tables for environment: {environment}\n")
    
    # Create tables
    create_users_table(dynamodb, tables['users'])
    create_schemes_table(dynamodb, tables['schemes'])
    create_user_profiles_table(dynamodb, tables['user_profiles'])
    create_interactions_table(dynamodb, tables['interactions'])
    create_farm_profiles_table(dynamodb, tables['farm_profiles'])
    
    print("\n✓ All tables created successfully!")
    print("\nTable Summary:")
    print(f"  - {tables['users']}: user_id (PK), phone_number (GSI)")
    print(f"  - {tables['schemes']}: scheme_id (PK), category (GSI)")
    print(f"  - {tables['user_profiles']}: user_id (PK)")
    print(f"  - {tables['interactions']}: user_id (PK), timestamp (SK)")
    print(f"  - {tables['farm_profiles']}: user_id (PK)")


if __name__ == '__main__':
    main()
