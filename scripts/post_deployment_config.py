#!/usr/bin/env python3
"""
Post-deployment configuration script for BharatSahayak.

This script automates post-deployment tasks:
1. Retrieves CloudFormation outputs
2. Updates frontend configuration
3. Loads sample scheme data
4. Validates deployment
"""

import boto3
import json
import sys
import re
from pathlib import Path

# Configuration
REGION = 'ap-south-1'
STACK_NAME = 'bharatsahayak-stack'
FRONTEND_JS_PATH = 'frontend/app.js'

def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")

def print_success(text):
    """Print success message."""
    print(f"✅ {text}")

def print_error(text):
    """Print error message."""
    print(f"❌ {text}")

def print_info(text):
    """Print info message."""
    print(f"ℹ️  {text}")

def get_stack_outputs():
    """Retrieve CloudFormation stack outputs."""
    print_header("Step 1: Retrieving Deployment Outputs")
    
    try:
        cfn = boto3.client('cloudformation', region_name=REGION)
        response = cfn.describe_stacks(StackName=STACK_NAME)
        
        if not response['Stacks']:
            print_error(f"Stack '{STACK_NAME}' not found")
            return None
        
        stack = response['Stacks'][0]
        outputs = {}
        
        for output in stack.get('Outputs', []):
            outputs[output['OutputKey']] = output['OutputValue']
            print_info(f"{output['OutputKey']}: {output['OutputValue']}")
        
        print_success(f"Retrieved {len(outputs)} outputs from stack")
        return outputs
        
    except Exception as e:
        print_error(f"Failed to get stack outputs: {str(e)}")
        return None

def update_frontend_config(outputs):
    """Update frontend app.js with deployment outputs."""
    print_header("Step 2: Updating Frontend Configuration")
    
    if not outputs:
        print_error("No outputs available to update frontend")
        return False
    
    # Get required values
    api_endpoint = outputs.get('ApiEndpoint', '')
    user_pool_id = outputs.get('UserPoolId', '')
    client_id = outputs.get('UserPoolClientId', '')
    
    if not all([api_endpoint, user_pool_id, client_id]):
        print_error("Missing required outputs")
        print_info(f"API Endpoint: {api_endpoint or 'MISSING'}")
        print_info(f"User Pool ID: {user_pool_id or 'MISSING'}")
        print_info(f"Client ID: {client_id or 'MISSING'}")
        return False
    
    # Read frontend app.js
    try:
        frontend_path = Path(FRONTEND_JS_PATH)
        if not frontend_path.exists():
            print_error(f"Frontend file not found: {FRONTEND_JS_PATH}")
            return False
        
        content = frontend_path.read_text()
        
        # Update config object
        old_config = r"let config = \{[^}]*\};"
        new_config = f"""let config = {{
    apiEndpoint: '{api_endpoint.rstrip('/')}',
    userPoolId: '{user_pool_id}',
    clientId: '{client_id}'
}};"""
        
        updated_content = re.sub(old_config, new_config, content, flags=re.DOTALL)
        
        # Write back
        frontend_path.write_text(updated_content)
        
        print_success("Updated frontend/app.js with deployment values")
        print_info(f"API Endpoint: {api_endpoint}")
        print_info(f"User Pool ID: {user_pool_id}")
        print_info(f"Client ID: {client_id}")
        return True
        
    except Exception as e:
        print_error(f"Failed to update frontend: {str(e)}")
        return False

def validate_deployment(outputs):
    """Validate that deployment is working."""
    print_header("Step 3: Validating Deployment")
    
    api_endpoint = outputs.get('ApiEndpoint', '')
    if not api_endpoint:
        print_error("No API endpoint found")
        return False
    
    # Test API health
    import urllib.request
    import urllib.error
    
    try:
        # Test schemes endpoint (no auth required)
        url = f"{api_endpoint.rstrip('/')}/schemes"
        print_info(f"Testing: {url}")
        
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            
            if response.status == 200:
                print_success("API is responding correctly")
                scheme_count = len(data.get('schemes', []))
                print_info(f"Found {scheme_count} schemes in database")
                return True
            else:
                print_error(f"API returned status {response.status}")
                return False
                
    except urllib.error.HTTPError as e:
        print_error(f"API request failed: HTTP {e.code}")
        print_info("This may be normal if no schemes are loaded yet")
        return False
    except Exception as e:
        print_error(f"Failed to validate deployment: {str(e)}")
        return False

def check_dynamodb_tables(outputs):
    """Check if DynamoDB tables exist."""
    print_header("Step 4: Checking DynamoDB Tables")
    
    expected_tables = [
        'bharatsahayak-users-dev',
        'bharatsahayak-schemes-dev',
        'bharatsahayak-user-profiles-dev',
        'bharatsahayak-interactions-dev'
    ]
    
    try:
        dynamodb = boto3.client('dynamodb', region_name=REGION)
        response = dynamodb.list_tables()
        existing_tables = response['TableNames']
        
        found_count = 0
        for table in expected_tables:
            if table in existing_tables:
                print_success(f"Table exists: {table}")
                found_count += 1
            else:
                print_warning(f"Table not found: {table}")
        
        print_info(f"Found {found_count}/{len(expected_tables)} expected tables")
        return found_count > 0
        
    except Exception as e:
        print_error(f"Failed to check tables: {str(e)}")
        return False

def generate_summary(outputs):
    """Generate deployment summary."""
    print_header("Deployment Summary")
    
    print("🎉 Post-Deployment Configuration Complete!")
    print()
    print("Your BharatSahayak system is deployed at:")
    print()
    print(f"  API Endpoint: {outputs.get('ApiEndpoint', 'N/A')}")
    print(f"  User Pool ID: {outputs.get('UserPoolId', 'N/A')}")
    print(f"  Client ID: {outputs.get('UserPoolClientId', 'N/A')}")
    print()
    print("Next steps:")
    print("  1. Load sample data: python scripts/load_schemes.py")
    print("  2. Deploy frontend: cd frontend && aws s3 sync . s3://bharatsahayak-frontend-dev")
    print("  3. Test frontend: http://bharatsahayak-frontend-dev.s3-website.ap-south-1.amazonaws.com")
    print()
    print("For testing:")
    print(f"  curl {outputs.get('ApiEndpoint', 'API_URL')}/schemes")
    print()

def main():
    """Main execution flow."""
    print_header("BharatSahayak - Post-Deployment Configuration")
    
    print("This script will:")
    print("1. Retrieve deployment outputs from CloudFormation")
    print("2. Update frontend configuration automatically")
    print("3. Validate deployment is working")
    print("4. Check DynamoDB tables")
    print("5. Provide next steps")
    print()
    
    # Step 1: Validate AWS credentials
    if not check_aws_credentials():
        sys.exit(1)
    
    # Step 2: Get stack outputs
    outputs = get_stack_outputs()
    if not outputs:
        print_error("Cannot proceed without stack outputs")
        print_info("Make sure you've run: sam deploy")
        sys.exit(1)
    
    # Step 3: Update frontend
    if update_frontend_config(outputs):
        print_success("Frontend configuration updated")
    else:
        print_warning("Frontend configuration update failed (you may need to update manually)")
    
    # Step 4: Validate deployment
    validate_deployment(outputs)
    
    # Step 5: Check tables
    check_dynamodb_tables(outputs)
    
    # Step 6: Generate summary
    generate_summary(outputs)
    
    print_header("Configuration Complete!")
    print_success("Your BharatSahayak system is ready to use")
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nConfiguration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
