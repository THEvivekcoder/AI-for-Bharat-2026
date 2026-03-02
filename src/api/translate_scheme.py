"""Lambda function to translate scheme content."""

import json
import os
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

from src.services.translate_service import TranslateService


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Translate scheme content to multiple languages.
    
    Expected input:
    {
        "scheme_id": "PM-KISAN-2024",
        "name": "Pradhan Mantri Kisan Samman Nidhi",
        "description": "Income support scheme for farmers...",
        "target_languages": ["hi", "ta", "te", "bn"]
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "scheme_id": "PM-KISAN-2024",
            "name_translations": {"hi": "...", "ta": "...", ...},
            "description_translations": {"hi": "...", "ta": "...", ...}
        }
    }
    """
    try:
        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        scheme_id = body.get('scheme_id')
        name = body.get('name')
        description = body.get('description')
        target_languages = body.get('target_languages', ['hi', 'ta', 'te', 'bn'])
        
        # Validate input
        if not scheme_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'scheme_id is required'})
            }
        
        if not name or not description:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'name and description are required'})
            }
        
        # Initialize translate service
        translate_service = TranslateService()
        
        # Validate target languages
        supported_languages = translate_service.get_supported_languages()
        invalid_languages = [lang for lang in target_languages if lang not in supported_languages]
        if invalid_languages:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': f'Unsupported languages: {", ".join(invalid_languages)}',
                    'supported_languages': supported_languages
                })
            }
        
        # Translate content
        scheme_data = {
            'name': name,
            'description': description
        }
        
        translations = translate_service.translate_scheme_content(scheme_data, target_languages)
        
        # Optionally update DynamoDB with translations
        if os.environ.get('UPDATE_DYNAMODB', 'false').lower() == 'true':
            _update_scheme_translations(scheme_id, translations)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'scheme_id': scheme_id,
                'name_translations': translations['name_translations'],
                'description_translations': translations['description_translations']
            })
        }
    
    except ValueError as e:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
    
    except Exception as e:
        print(f"Error translating scheme: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }


def _update_scheme_translations(scheme_id: str, translations: Dict) -> None:
    """Update scheme translations in DynamoDB."""
    try:
        dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        table_name = os.environ.get('SCHEMES_TABLE', 'BharatSahayak-Schemes')
        table = dynamodb.Table(table_name)
        
        # Update the scheme with translations
        table.update_item(
            Key={'scheme_id': scheme_id},
            UpdateExpression='SET name_translations = :nt, description_translations = :dt',
            ExpressionAttributeValues={
                ':nt': translations['name_translations'],
                ':dt': translations['description_translations']
            }
        )
    except Exception as e:
        print(f"Failed to update DynamoDB: {str(e)}")
        # Don't fail the request if DynamoDB update fails
