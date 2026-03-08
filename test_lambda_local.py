#!/usr/bin/env python3
"""Test Lambda function locally to debug issues."""

import os
import sys

# Set environment variables
os.environ['SCHEMES_TABLE'] = 'bharatsahayak-schemes-dev'
os.environ['AWS_DEFAULT_REGION'] = 'ap-south-1'
os.environ['LOG_LEVEL'] = 'DEBUG'

# Import the handler
try:
    from src.api.schemes_search import lambda_handler
    
    # Test event
    event = {
        'queryStringParameters': {}
    }
    
    # Invoke handler
    result = lambda_handler(event, None)
    print("Success!")
    print(result)
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
