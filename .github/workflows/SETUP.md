# GitHub Actions + AWS ECR Setup Guide

This workflow automatically builds and pushes your Docker image to AWS ECR whenever you push to `main`.

## Architecture

```
git push → GitHub Actions (ubuntu-latest) → Build Docker → Push to ECR → Ready for SageMaker
                                                                              ↓
                                                                    sagemaker_config.py
                                                                    (uses ECR image URI)
```

---

## Setup (One-Time)

### Option A: IAM User + Keys (Simpler)

#### 1. Create IAM User in AWS Console

```bash
# Using AWS CLI
aws iam create-user --user-name github-actions
```

#### 2. Create IAM Policy (ECR-only access)

Go to AWS Console → IAM → Policies → Create Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "arn:aws:ecr:us-east-1:ACCOUNT_ID:repository/sagemaker-mlops"
    }
  ]
}
```

#### 3. Attach Policy to User

```bash
aws iam attach-user-policy \
  --user-name github-actions \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/GitHubActionsECR
```

#### 4. Create Access Keys

```bash
aws iam create-access-key --user-name github-actions
```

Save output:
```
AccessKeyId: AKIA...
SecretAccessKey: ...
```

#### 5. Add Secrets to GitHub

Go to your GitHub repo → Settings → Secrets and Variables → Actions → New repository secret

Add these secrets:
- `AWS_ACCESS_KEY_ID` = AccessKeyId from step 4
- `AWS_SECRET_ACCESS_KEY` = SecretAccessKey from step 4
- `AWS_ACCOUNT_ID` = Your AWS account ID (12 digits)

---

### Option B: OIDC (More Secure, No Keys)

#### 1. Create IAM Role in AWS

This allows GitHub to assume a role without storing credentials.

```bash
# Create role with OIDC provider
# See: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect
```

#### 2. Add to GitHub Secrets

- `AWS_ROLE_ARN` = arn:aws:iam::ACCOUNT_ID:role/github-actions-role

Then uncomment the OIDC section in workflow:
```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    aws-region: us-east-1
```

**Recommendation**: Use Option B for production (more secure), Option A for quick setup.

---

## Verify Setup

### 1. Test ECR Access

```bash
# Authenticate with AWS
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Try pushing a test image
docker tag hello-world:latest \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/sagemaker-mlops:test

docker push \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/sagemaker-mlops:test
```

If this works, GitHub Actions will work too.

### 2. Check Workflow Runs

Push a commit with changes to `Dockerfile` or `training/`:

```bash
git add .github/workflows/docker-build-push.yml
git commit -m "Add GitHub Actions workflow for ECR"
git push origin main
```

Then go to GitHub → Actions tab → Watch the workflow run

---

## How It Works

### Trigger Events

The workflow runs when you:
1. **Push to main** AND modify:
   - `Dockerfile`
   - `training/**` (any training code)
   - `inference/**` (any inference code)
   - `models/**` (model definitions)
   - `.github/workflows/docker-build-push.yml` (workflow itself)

2. **Manual trigger** via GitHub Actions UI

### What Happens

```
Step 1: Checkout code from GitHub
Step 2: Authenticate with AWS (using secrets)
Step 3: Login to ECR
Step 4: Build Docker image (docker build .)
Step 5: Push to ECR with 2 tags:
        - sagemaker-mlops:COMMIT_SHA (specific version)
        - sagemaker-mlops:latest (always latest)
Step 6: Print image URI for SageMaker
```

### Runner Machine

```
runs-on: ubuntu-latest  ← GitHub-hosted runner
├─ Specs:
│  ├─ CPU: 2 vCPU
│  ├─ RAM: 7 GB
│  ├─ Disk: 14 GB
│  └─ Cost: Free (2000 min/month)
├─ Pre-installed:
│  ├─ Docker
│  ├─ Python 3.11
│  └─ AWS CLI
└─ Location: Shared GitHub data center
```

---

## Using the Built Image in SageMaker

After the workflow succeeds, use the image URI in your code:

```python
from sagemaker.estimator import Estimator
from sagemaker_config import get_training_image_uri

# Option 1: Use latest
image_uri = f"{AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/sagemaker-mlops:latest"

# Option 2: Use specific commit
image_uri = f"{AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/sagemaker-mlops:abc1234567..."

# Train with it
estimator = Estimator(
    image_uri=image_uri,
    role=role,
    instance_type='ml.p3.2xlarge',
    ...
)
estimator.fit(training_data)
```

Or update `sagemaker_config.py`:
```python
ECR_IMAGE_URI = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPO_NAME}:latest"
```

---

## Advanced: Self-Hosted Runners

If you need GPU for building (e.g., pre-building model artifacts):

```yaml
runs-on: [self-hosted, gpu]  # Use your own machine
```

Requires:
1. EC2 instance running GitHub Actions runner software
2. Docker installed
3. GPU (optional, for large builds)

**Cost**: $0.008 per minute + EC2 instance cost
**Use case**: Only if build takes > 1 hour consistently

---

## Troubleshooting

### Build fails: "AWS credentials not configured"
- Check GitHub Secrets are set: Settings → Secrets and Variables → Actions
- Verify secret names match workflow (case-sensitive)
- Test locally: `aws ecr get-login-password --region us-east-1`

### Build fails: "Permission denied: /var/run/docker.sock"
- GitHub-hosted runners have Docker by default
- If using self-hosted, ensure runner user has Docker permissions: `sudo usermod -aG docker $USER`

### Image push fails: "repository does not exist"
- Create ECR repo first:
  ```bash
  aws ecr create-repository --repository-name sagemaker-mlops --region us-east-1
  ```

### Workflow doesn't trigger
- Check file paths in `paths` section match your changes
- Try manual trigger: Actions → docker-build-push → Run workflow

---

## Secrets Reference

| Secret | Source | Example |
|--------|--------|---------|
| `AWS_ACCESS_KEY_ID` | IAM User → Create Access Key | `AKIA2345678...` |
| `AWS_SECRET_ACCESS_KEY` | IAM User → Create Access Key | `wJalr...` |
| `AWS_ACCOUNT_ID` | AWS Console (top-right) | `123456789012` |
| `AWS_ROLE_ARN` | OIDC Setup (if using Option B) | `arn:aws:iam::123456789012:role/...` |

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ Scenario: You push changes to Dockerfile                │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ GitHub detects push to main with Dockerfile change      │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ GitHub Actions spawns ubuntu-latest runner              │
│ (2 vCPU, 7GB RAM, Docker pre-installed)                 │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ Workflow runs:                                          │
│ 1. Checkout code from your repo                         │
│ 2. Configure AWS credentials (from GitHub Secrets)      │
│ 3. Login to ECR                                         │
│ 4. docker build -t image:tag .                          │
│ 5. docker push image:tag to ECR                         │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ ✅ Image ready in ECR for SageMaker training            │
│    sagemaker-mlops:latest                              │
│    sagemaker-mlops:COMMIT_SHA                          │
└─────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. ✅ Create IAM user with ECR permissions
2. ✅ Add AWS credentials to GitHub Secrets
3. ✅ Verify workflow file exists: `.github/workflows/docker-build-push.yml`
4. ✅ Make a test commit with Dockerfile change
5. ✅ Check Actions tab to verify workflow runs
6. ✅ Use image URI in SageMaker training

---

## See Also

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS ECR Login Action](https://github.com/aws-actions/amazon-ecr-login)
- [GitHub OIDC Provider](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [SageMaker Training with Custom Docker](https://docs.aws.amazon.com/sagemaker/latest/dg/docker-containers-adapt.html)
