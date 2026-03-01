# BharatSahayak - Makefile for Deployment and Testing
# Usage: make <target>

.PHONY: help install test deploy clean setup-aws load-data deploy-frontend all

# Default target
help:
	@echo "BharatSahayak - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install          - Install Python dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-property    - Run property-based tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make coverage         - Run tests with coverage report"
	@echo "  make lint             - Run code linting"
	@echo ""
	@echo "AWS Deployment:"
	@echo "  make setup-aws        - Create all AWS resources (DynamoDB, S3, Cognito)"
	@echo "  make deploy-lambda    - Build and deploy Lambda functions"
	@echo "  make deploy-frontend  - Deploy frontend to S3"
	@echo "  make load-data        - Load sample scheme data to DynamoDB"
	@echo "  make deploy-all       - Complete deployment (AWS + Lambda + Frontend + Data)"
	@echo ""
	@echo "Utilities:"
	@echo "  make logs             - Tail Lambda function logs"
	@echo "  make validate         - Validate SAM template"
	@echo "  make clean            - Clean build artifacts"
	@echo "  make destroy          - Delete all AWS resources (CAUTION!)"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make install"
	@echo "  2. Configure .env file with your AWS credentials"
	@echo "  3. make deploy-all"
	@echo ""

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "✓ Dependencies installed"

# Run all tests
test:
	@echo "Running all tests..."
	python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term
	@echo "✓ Tests complete. Coverage report: htmlcov/index.html"

# Run unit tests only
test-unit:
	@echo "Running unit tests..."
	python -m pytest tests/unit/ -v
	@echo "✓ Unit tests complete"

# Run property-based tests only
test-property:
	@echo "Running property-based tests..."
	python -m pytest tests/property/ -v
	@echo "✓ Property tests complete"

# Run integration tests only
test-integration:
	@echo "Running integration tests..."
	python -m pytest tests/integration/ -v
	@echo "✓ Integration tests complete"

# Run tests with coverage
coverage:
	@echo "Running tests with coverage..."
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
	@echo "✓ Coverage report generated: htmlcov/index.html"

# Lint code
lint:
	@echo "Running linters..."
	python -m pylint src/ --disable=C0111,R0903
	@echo "✓ Linting complete"

# Validate SAM template
validate:
	@echo "Validating SAM template..."
	sam validate
	@echo "✓ Template is valid"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf .aws-sam/
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned"

# Setup AWS resources
setup-aws:
	@echo "Creating AWS resources..."
	@echo ""
	@echo "Step 1: Creating DynamoDB tables..."
	@bash -c ' \
		aws dynamodb create-table \
			--table-name BharatSahayak-Users \
			--attribute-definitions AttributeName=user_id,AttributeType=S \
			--key-schema AttributeName=user_id,KeyType=HASH \
			--billing-mode PAY_PER_REQUEST \
			--region us-east-1 2>/dev/null || echo "Users table already exists"; \
		aws dynamodb create-table \
			--table-name BharatSahayak-Schemes \
			--attribute-definitions AttributeName=scheme_id,AttributeType=S AttributeName=category,AttributeType=S \
			--key-schema AttributeName=scheme_id,KeyType=HASH \
			--global-secondary-indexes "[{\"IndexName\":\"category-index\",\"KeySchema\":[{\"AttributeName\":\"category\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]" \
			--billing-mode PAY_PER_REQUEST \
			--region us-east-1 2>/dev/null || echo "Schemes table already exists"; \
		aws dynamodb create-table \
			--table-name BharatSahayak-UserProfiles \
			--attribute-definitions AttributeName=user_id,AttributeType=S \
			--key-schema AttributeName=user_id,KeyType=HASH \
			--billing-mode PAY_PER_REQUEST \
			--region us-east-1 2>/dev/null || echo "UserProfiles table already exists"; \
		aws dynamodb create-table \
			--table-name BharatSahayak-Interactions \
			--attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=timestamp,AttributeType=S \
			--key-schema AttributeName=user_id,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
			--billing-mode PAY_PER_REQUEST \
			--region us-east-1 2>/dev/null || echo "Interactions table already exists"; \
	'
	@echo "✓ DynamoDB tables created"
	@echo ""
	@echo "Step 2: Creating S3 bucket..."
	@bash -c ' \
		aws s3 mb s3://bharatsahayak-content --region us-east-1 2>/dev/null || echo "S3 bucket already exists"; \
		aws s3api put-bucket-versioning --bucket bharatsahayak-content --versioning-configuration Status=Enabled 2>/dev/null; \
	'
	@echo "✓ S3 bucket created"
	@echo ""
	@echo "Step 3: Creating Cognito User Pool..."
	@echo "⚠ Manual step required: Run the following commands and update .env file:"
	@echo ""
	@echo "aws cognito-idp create-user-pool \\"
	@echo "    --pool-name BharatSahayak-Users \\"
	@echo "    --username-attributes phone_number \\"
	@echo "    --auto-verified-attributes phone_number \\"
	@echo "    --region us-east-1"
	@echo ""
	@echo "Then create app client with the UserPoolId from above:"
	@echo "aws cognito-idp create-user-pool-client \\"
	@echo "    --user-pool-id YOUR_USER_POOL_ID \\"
	@echo "    --client-name BharatSahayak-Client \\"
	@echo "    --no-generate-secret \\"
	@echo "    --region us-east-1"
	@echo ""
	@echo "✓ AWS resources setup initiated"

# Deploy Lambda functions
deploy-lambda:
	@echo "Building SAM application..."
	sam build
	@echo "✓ Build complete"
	@echo ""
	@echo "Deploying to AWS..."
	sam deploy
	@echo "✓ Lambda functions deployed"
	@echo ""
	@echo "Getting API Gateway URL..."
	@bash -c 'aws cloudformation describe-stacks \
		--stack-name bharatsahayak-stack \
		--query "Stacks[0].Outputs[?OutputKey==\`ApiUrl\`].OutputValue" \
		--output text'
	@echo ""
	@echo "⚠ Update .env file with the API_GATEWAY_URL above"

# Load sample data
load-data:
	@echo "Loading sample scheme data..."
	python scripts/load_schemes.py
	@echo "✓ Sample data loaded"

# Deploy frontend
deploy-frontend:
	@echo "Deploying frontend to S3..."
	@bash -c ' \
		aws s3 mb s3://bharatsahayak-frontend --region us-east-1 2>/dev/null || echo "Frontend bucket exists"; \
		aws s3 website s3://bharatsahayak-frontend --index-document index.html --error-document index.html; \
		cd frontend && aws s3 sync . s3://bharatsahayak-frontend --exclude "*.sh" --exclude "*.md" --exclude "DEPLOYMENT.md"; \
	'
	@echo "✓ Frontend deployed"
	@echo ""
	@echo "Frontend URL: http://bharatsahayak-frontend.s3-website-us-east-1.amazonaws.com"

# Complete deployment
deploy-all: setup-aws deploy-lambda load-data deploy-frontend
	@echo ""
	@echo "=========================================="
	@echo "✓ Complete deployment finished!"
	@echo "=========================================="
	@echo ""
	@echo "Next steps:"
	@echo "1. Update .env file with Cognito User Pool ID and Client ID"
	@echo "2. Update frontend/app.js with API Gateway URL"
	@echo "3. Test the application"
	@echo ""
	@echo "Frontend: http://bharatsahayak-frontend.s3-website-us-east-1.amazonaws.com"
	@echo ""

# View Lambda logs
logs:
	@echo "Tailing Lambda logs (Ctrl+C to exit)..."
	sam logs -n AuthRegisterFunction --tail

# Destroy all AWS resources
destroy:
	@echo "⚠ WARNING: This will delete all AWS resources!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	@echo "Deleting CloudFormation stack..."
	sam delete --stack-name bharatsahayak-stack --no-prompts
	@echo "Deleting DynamoDB tables..."
	@bash -c ' \
		aws dynamodb delete-table --table-name BharatSahayak-Users --region us-east-1 2>/dev/null || true; \
		aws dynamodb delete-table --table-name BharatSahayak-Schemes --region us-east-1 2>/dev/null || true; \
		aws dynamodb delete-table --table-name BharatSahayak-UserProfiles --region us-east-1 2>/dev/null || true; \
		aws dynamodb delete-table --table-name BharatSahayak-Interactions --region us-east-1 2>/dev/null || true; \
	'
	@echo "Deleting S3 buckets..."
	@bash -c ' \
		aws s3 rb s3://bharatsahayak-content --force 2>/dev/null || true; \
		aws s3 rb s3://bharatsahayak-frontend --force 2>/dev/null || true; \
	'
	@echo "✓ All resources deleted"

# Quick development setup
dev-setup: install
	@echo "Setting up development environment..."
	@echo "✓ Development environment ready"
	@echo ""
	@echo "Next steps:"
	@echo "1. Copy .env.example to .env and configure"
	@echo "2. Run 'make test' to verify setup"
	@echo "3. Run 'make deploy-all' when ready to deploy"
