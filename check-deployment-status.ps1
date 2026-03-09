# Check Deployment Status

$env:Path += ";C:\Program Files\Amazon\AWSCLIV2"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Checking Deployment Status" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check stack status
Write-Host "Stack Status:" -ForegroundColor Yellow
aws cloudformation describe-stacks `
  --stack-name bharatsahayak-dev `
  --region us-east-1 `
  --query 'Stacks[0].StackStatus' `
  --output text

Write-Host ""

# If stack is complete, show outputs
$status = aws cloudformation describe-stacks `
  --stack-name bharatsahayak-dev `
  --region us-east-1 `
  --query 'Stacks[0].StackStatus' `
  --output text

if ($status -eq "CREATE_COMPLETE" -or $status -eq "UPDATE_COMPLETE") {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Deployment Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "API Gateway Endpoint:" -ForegroundColor Cyan
    $apiEndpoint = aws cloudformation describe-stacks `
      --stack-name bharatsahayak-dev `
      --region us-east-1 `
      --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' `
      --output text
    
    Write-Host $apiEndpoint -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Update frontend/config.json with this API endpoint:" -ForegroundColor White
    Write-Host "   {`"apiEndpoint`": `"$apiEndpoint`"}" -ForegroundColor White
    Write-Host ""
    Write-Host "2. Open frontend/login.html in your browser" -ForegroundColor White
    Write-Host "3. Register with email and password" -ForegroundColor White
    Write-Host "4. Test the complete flow!" -ForegroundColor White
    Write-Host ""
    Write-Host "JWT Secret (save this): To2gBlws9qRhc8HNj7SALGfXzWdYeyZv" -ForegroundColor Yellow
    
} elseif ($status -like "*IN_PROGRESS*") {
    Write-Host "Deployment still in progress..." -ForegroundColor Yellow
    Write-Host "Run this script again in a few minutes to check status." -ForegroundColor White
    Write-Host ""
    Write-Host "Or monitor in AWS Console:" -ForegroundColor Cyan
    Write-Host "https://console.aws.amazon.com/cloudformation/home?region=us-east-1" -ForegroundColor White
    
} elseif ($status -like "*FAILED*" -or $status -like "*ROLLBACK*") {
    Write-Host "Deployment failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check the error:" -ForegroundColor Yellow
    aws cloudformation describe-stack-events `
      --stack-name bharatsahayak-dev `
      --region us-east-1 `
      --max-items 5 `
      --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' `
      --output table
} else {
    Write-Host "Unknown status: $status" -ForegroundColor Yellow
}

Write-Host ""
