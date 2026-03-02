"""Lambda function for language detection."""
import json
import os
from typing import Dict, Any
from src.services.comprehend_service import ComprehendService


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for language detection.
    
    Expects:
        - text: Text to analyze for language detection
        OR
        - texts: List of texts for batch detection (max 25)
    
    Returns:
        Language detection result(s) with language code and confidence
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Check for single or batch mode
        text = body.get('text')
        texts = body.get('texts')
        
        if not text and not texts:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'text or texts is required'})
            }
        
        # Initialize Comprehend service
        comprehend_service = ComprehendService()
        
        # Single text detection
        if text:
            result = comprehend_service.detect_language(text)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'language_code': result['language_code'],
                    'confidence': result['confidence'],
                    'all_languages': result['all_languages']
                })
            }
        
        # Batch text detection
        if texts:
            if not isinstance(texts, list):
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'texts must be a list'})
                }
            
            if len(texts) > 25:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'maximum 25 texts allowed in batch'})
                }
            
            results = comprehend_service.detect_language_batch(texts)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'results': results
                })
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
