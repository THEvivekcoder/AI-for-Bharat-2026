# BharatSahayak - IAM Permissions Required

## 🚨 Deployment Blocked - Insufficient IAM Permissions

Your IAM user `BharatSahayak` doesn't have the required permissions to deploy the application.

---

## ❌ Current Error

```
User: arn:aws:iam::390402557080:user/BharatSahayak is not authorized to perform:
cloudformation:CreateChangeSet
```

This means your user cannot create CloudFormation stacks, which is required for SAM deployment.

---

## ✅ Required Permissions

To deploy BharatSahayak, your IAM user needs permissions for:

1. **CloudFormation** - Create and manage stacks
2. **Lambda** - Deploy functions
3. **DynamoDB** - Create tables
4. **S3** - Create buckets and upload code
5. **Cognito** - Create user pools
6. **IAM** - Create roles for Lambda functions
7. **API Gateway** - Create REST APIs
8. **CloudWatch** - Create log groups

---

## 🔧 Solution Options

### Option 1: Attach AdministratorAccess Policy (Easiest)

**⚠️ Warning:** This gives full AWS access. Only use for testing/development.

**Steps:**
1. Go to AWS Console: https://console.aws.amazon.com/iam/
2. Navigate to: **IAM → Users → BharatSahayak**
3. Click **"Add permissions"** → **"Attach policies directly"**
4. Search for: **AdministratorAccess**
5. Check the box next to it
6. Click **"Add permissions"**

**Then retry deployment:**
```bash
sam deploy --guided --region ap-south-1
```

---

### Option 2: Attach Specific Policies (More Secure)

Attach these AWS managed policies:

1. **AWSCloudFormationFullAccess**
2. **AWSLambda_FullAccess**
3. **AmazonDynamoDBFullAccess**
4. **AmazonS3FullAccess**
5. **AmazonCognitoPowerUser**
6. **IAMFullAccess**
7. **AmazonAPIGatewayAdministrator**
8. **CloudWatchLogsFullAccess**

**Steps:**
1. Go to AWS Console: https://console.aws.amazon.com/iam/
2. Navigate to: **IAM → Users → BharatSahayak**
3. Click **"Add permissions"** → **"Attach policies directly"**
4. Search and attach each policy above
5. Click **"Add permissions"**

---

### Option 3: Create Custom Policy (Most Secure)

Create a custom policy with minimal required permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "lambda:*",
        "dynamodb:*",
        "s3:*",
        "cognito-idp:*",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:PassRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "apigateway:*",
        "logs:*",
        "sns:*"
      ],
      "Resource": "*"
    }
  ]
}
```

**Steps:**
1. Go to AWS Console: https://console.aws.amazon.com/iam/
2. Navigate to: **IAM → Policies → Create policy**
3. Click **JSON** tab
4. Paste the policy above
5. Name it: **BharatSahayakDeploymentPolicy**
6. Create policy
7. Go to: **IAM → Users → BharatSahayak**
8. Attach the new policy

---

### Option 4: Use Different IAM User

If you have another IAM user with admin access:

```bash
# Configure with different credentials
aws configure --profile admin

# Deploy using that profile
sam deploy --guided --region ap-south-1 --profile admin
```

---

## 🎯 Recommended Approach

**For Student Project / Testing:**
→ Use **Option 1** (AdministratorAccess)
- Fastest to set up
- No permission issues
- Can revoke after project is done

**For Production / Team Project:**
→ Use **Option 2** (Specific Policies)
- More secure
- Follows least privilege principle
- Still comprehensive enough

---

## 📋 Step-by-Step: Add AdministratorAccess

1. **Open AWS Console:**
   - Go to: https://console.aws.amazon.com/iam/

2. **Navigate to your user:**
   - Click **"Users"** in left sidebar
   - Click **"BharatSahayak"**

3. **Add permissions:**
   - Click **"Add permissions"** button
   - Select **"Attach policies directly"**

4. **Search and attach:**
   - In search box, type: **AdministratorAccess**
   - Check the box next to **AdministratorAccess**
   - Click **"Add permissions"** button

5. **Verify:**
   - You should see **AdministratorAccess** in the permissions list

6. **Retry deployment:**
   ```bash
   sam deploy --guided --region ap-south-1
   ```

---

## ⏱️ Time Estimate

- Add permissions in AWS Console: 2 minutes
- Retry deployment: 15 minutes
- **Total: 17 minutes**

---

## 🔒 Security Note

**After your project is complete**, you can:
- Remove AdministratorAccess
- Add only the specific permissions you need
- Or delete the IAM user entirely

For a student project, AdministratorAccess is fine during development.

---

## ✅ After Adding Permissions

Once permissions are added, we'll continue with:

1. ✅ Run `sam deploy --guided`
2. ✅ Enter JWT secret when prompted: `-GRKd3337BNuZh2WPNcfMmGTUCkJKizIEl-r8QoNrxM`
3. ✅ Confirm deployment
4. ✅ Wait 10-15 minutes for deployment
5. ✅ Configure frontend
6. ✅ Load sample data
7. ✅ Test the application

---

**NEXT STEP:** Add AdministratorAccess policy to your IAM user in AWS Console, then let me know when done!