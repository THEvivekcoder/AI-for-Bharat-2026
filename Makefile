# BharatSahayak - Makefile for Deployment and Testing
# Usage: make <target>

.PHONY: help install test deploy clean setup-aws load-data deploy-frontend all setup-secrets

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
	@echo "  make setup-secrets    - Create JWT secret in AWS Secrets Manager (REQUIRED FIRST)"
	@echo "  make setup-aws        - Info about AWS resource automation"
	@echo "  make deploy-lambda    - Build and deploy ALL AWS resources via SAM"
	@echo "  make deploy-frontend  - Deploy frontend to S3"
	@echo "  make load-data        - Load sample scheme data to DynamoDB"
	@echo "  make deploy-all       - Complete deployment (Lambda + Frontend + Data)"
	@echo ""
	@echo "Utilities:"
	@echo "  make logs             - Tail Lambda function logs"
	@echo "  make validate         - Validate SAM template"
	@echo "  make clean            - Clean build artifacts"
	@echo "  make destroy          - Delete all AWS resources (CAUTION!)"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make install"
	@echo "  2. aws configure (enter your AWS credentials)"
	@echo "  3. make setup-secrets (create JWT secret)"
	@echo "  4. make deploy-all (deploy everything)"
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

# Setup JWT secret in AWS Secrets Manager (REQUIRED BEFORE DEPLOYMENT)
setup-secrets:
	@echo "=========================================="
	@echo "Creating JWT Secret in AWS Secrets Manager"
	@echo "=========================================="
	@echo ""
	@echo "Generating secure JWT secret..."
	@bash -c ' \
		JWT_SECRET=$$(python -c "import secrets; print(secrets.token_urlsafe(32))"); \
		echo "Generated secret: $$JWT_SECRET"; \
		echo ""; \
		echo "Creating secret in AWS Secrets Manager..."; \
		aws secretsmanager create-secret \
			--name bharatsahayak-jwt-secret-dev \
			--description "JWT secret for BharatSahayak dev environment" \
			--secret-string "{\"jwt_secret\":\"$$JWT_SECRET\"}" \
			--region ap-south-1 2>/dev/null && echo "✓ Secret created successfully!" || echo "⚠ Secret already exists (this is OK)"; \
	'
	@echo ""
	@echo "✓ JWT secret setup complete!"
	@echo ""
	@echo "For production, run:"
	@echo "  aws secretsmanager create-secret \\"
	@echo "    --name bharatsahayak-jwt-secret-prod \\"
	@echo "    --secret-string '{\"jwt_secret\":\"YOUR_PROD_SECRET\"}' \\"
	@echo "    --region ap-south-1"
	@echo ""

# Setup AWS resources (AUTOMATED via SAM)
setup-aws:
	@echo "=========================================="
	@echo "AWS Resource Setup"
	@echo "=========================================="
	@echo ""
	@echo "✓ Good news: AWS resources are FULLY AUTOMATED via SAM template!"
	@echo ""
	@echo "The template.yaml file defines:"
	@echo "  • 10 DynamoDB tables"
	@echo "  • 3 S3 buckets with policies"
	@echo "  • Cognito User Pool with SMS OTP"
	@echo "  • 24 Lambda functions"
	@echo "  • API Gateway with CORS"
	@echo "  • OpenSearch domain for RAG"
	@echo "  • IAM roles and permissions"
	@echo ""
	@echo "To deploy all resources, simply run:"
	@echo "  make deploy-lambda"
	@echo ""
	@echo "Or manually:"
	@echo "  sam build && sam deploy --guided"
	@echo ""
	@echo "=========================================="

# Deploy Lambda functions (FULLY AUTOMATED)
deploy-lambda:
	@echo "=========================================="
	@echo "Deploying BharatSahayak to AWS"
	@echo "=========================================="
	@echo ""
	@echo "Step 1: Validating SAM template..."
	sam validate --lint
	@echo "✓ Template is valid"
	@echo ""
	@echo "Step 2: Building application..."
	sam build
	@echo "✓ Build complete"
	@echo ""
	@echo "Step 3: Deploying to AWS..."
	@echo "(This will create ALL resources: DynamoDB, S3, Cognito, Lambda, API Gateway, OpenSearch)"
	sam deploy
	@echo ""
	@echo "✓ Deployment complete!"
	@echo ""
	@echo "=========================================="
	@echo "Getting deployment information..."
	@echo "=========================================="
	@bash -c 'aws cloudformation describe-stacks \
		--stack-name bharatsahayak \
		--query "Stacks[0].Outputs" \
		--output table'
	@echo ""
	@echo "⚠ IMPORTANT: Save the API endpoint URL above!"
	@echo "   Update frontend/app.js with this URL"
	@echo ""

# Load sample data
load-data:
	@echo "=========================================="
	@echo "Loading Sample Data"
	@echo "=========================================="
	@echo ""
	@echo "Loading government schemes..."
	python infrastructure/scripts/load_schemes.py --source sample
	@echo ""
	@echo "Loading skill programs and jobs..."
	python infrastructure/scripts/load_skills.py
	@echo ""
	@echo "Loading health facilities..."
	python infrastructure/scripts/load_health_facilities.py
	@echo ""
	@echo "✓ All sample data loaded successfully!"
	@echo ""

# Deploy frontend
deploy-frontend:
	@echo "=========================================="
	@echo "Deploying Frontend"
	@echo "=========================================="
	@echo ""
	@echo "⚠ IMPORTANT: Update frontend/app.js with your API URL first!"
	@echo ""
	@echo "Get your API URL:"
	@bash -c 'aws cloudformation describe-stacks \
		--stack-name bharatsahayak \
		--query "Stacks[0].Outputs[?OutputKey==\`ApiEndpoint\`].OutputValue" \
		--output text'
	@echo ""
	@read -p "Press Enter after updating frontend/app.js, or Ctrl+C to cancel..."
	@echo ""
	@echo "Deploying to S3..."
	@bash -c 'cd frontend && bash deploy.sh'
	@echo ""
	@echo "✓ Frontend deployed!"
	@echo ""
	@echo "Frontend URL: http://bharatsahayak-frontend-dev.s3-website.ap-south-1.amazonaws.com"
	@echo ""

# Complete deployment
deploy-all: setup-secrets deploy-lambda load-data deploy-frontend
	@echo ""
	@echo "=========================================="
	@echo "✓ DEPLOYMENT COMPLETE!"
	@echo "=========================================="
	@echo ""
	@echo "Your BharatSahayak system is now live!"
	@echo ""
	@echo "Resources created:"
	@echo "  ✓ 10 DynamoDB tables"
	@echo "  ✓ 3 S3 buckets"
	@echo "  ✓ 24 Lambda functions"
	@echo "  ✓ 1 API Gateway"
	@echo "  ✓ 1 Cognito User Pool"
	@echo "  ✓ 1 OpenSearch domain"
	@echo "  ✓ Sample data loaded (20+ schemes, 10 programs, 10 jobs)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Test the API endpoints"
	@echo "  2. Test the frontend"
	@echo "  3. Register a test user"
	@echo "  4. Search for schemes"
	@echo ""
	@echo "Useful commands:"
	@echo "  make logs          - View Lambda logs"
	@echo "  make test          - Run tests"
	@echo "  make destroy       - Delete all resources"
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


# Pre-deployment setup (automated)
pre-deploy:
	@echo "Running pre-deployment setup..."
	python scripts/pre_deployment_setup.py
	@echo "✓ Pre-deployment setup complete"

# Post-deployment configuration (automated)
post-deploy:
	@echo "Running post-deployment configuration..."
	python scripts/post_deployment_config.py
	@echo "✓ Post-deployment configuration complete"

# Complete automated deployment flow
deploy-complete: pre-deploy deploy-lambda post-deploy load-data deploy-frontend
	@echo ""
	@echo "=========================================="
	@echo "✅ Complete deployment finished!"
	@echo "=========================================="
	@echo ""
	@echo "Your BharatSahayak system is ready!"
	@echo ""
	@echo "Test it:"
	@echo "  Frontend: http://bharatsahayak-frontend-dev.s3-website.ap-south-1.amazonaws.com"
	@echo ""
