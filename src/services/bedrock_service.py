import boto3
import json
import os
from botocore.exceptions import ClientError


class BedrockService:
    """
    Handles all interactions with Amazon Bedrock:
    - Embeddings (Titan)
    - Text generation (Claude 3)
    """

    def __init__(self):
        self.region = os.environ.get("AWS_REGION", "us-east-1")

        self.generation_model_id = os.environ.get(
            "BEDROCK_MODEL_ID",
            "anthropic.claude-3-sonnet-20240229"
        )

        self.embedding_model_id = os.environ.get(
            "BEDROCK_EMBED_MODEL_ID",
            "amazon.titan-embed-text-v1"
        )

        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=self.region
        )

    # ===============================
    # EMBEDDING
    # ===============================
    def generate_embedding(self, text: str):
        try:
            body = json.dumps({
                "inputText": text
            })

            response = self.client.invoke_model(
                modelId=self.embedding_model_id,
                body=body
            )

            result = json.loads(response["body"].read())
            return result["embedding"]

        except ClientError as e:
            print(f"Embedding error: {e}")
            return []

    # ===============================
    # TEXT GENERATION (Claude 3)
    # ===============================
    def generate_response(self, prompt: str, max_tokens: int = 500, temperature: float = 0.3):
        try:
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            response = self.client.invoke_model(
                modelId=self.generation_model_id,
                body=json.dumps(body)
            )

            result = json.loads(response["body"].read())

            return result["content"][0]["text"]

        except ClientError as e:
            print(f"Generation error: {e}")
            return "I encountered an error while generating the response."