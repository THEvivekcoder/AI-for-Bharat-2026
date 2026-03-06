import json
from src.services.bedrock_service import BedrockService
from src.services.rag_engine import build_scheme_prompt
from src.services.scheme_service import get_filtered_schemes


def lambda_handler(event, context):

    body = json.loads(event["body"])

    user_query = body.get("query")
    gender = body.get("gender")
    state = body.get("state")
    category = body.get("category")

    # 1️⃣ Retrieve from DynamoDB
    schemes = get_filtered_schemes(gender, state, category)

    if not schemes:
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No matching schemes found."})
        }

    # 2️⃣ Build prompt
    prompt = build_scheme_prompt(user_query, schemes[:5])

    # 3️⃣ Call Bedrock
    bedrock = BedrockService()
    answer = bedrock.generate_response(prompt)

    return {
        "statusCode": 200,
        "body": json.dumps({"answer": answer})
    }