# GitHub Actions CI/CD Quick Start

## TL;DR: What's Automated

Every time you push code changes to `main`:
```
git push → GitHub builds Docker image → Pushes to AWS ECR → Ready for SageMaker
```

---

## 5-Minute Setup

### Step 1: Create ECR Repository (if not exists)

```bash
aws ecr create-repository \
  --repository-name sagemaker-mlops \
  --region us-east-1
```

Output:
```
repositoryUri: 123456789012.dkr.ecr.us-east-1.amazonaws.com/sagemaker-mlops
```

### Step 2: Create IAM User with ECR Permission

```bash
# Create user
aws iam create-user --user-name github-actions

# Create inline policy
aws iam put-user-policy --user-name github-actions \
  --policy-name ECRPushPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
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
      "Resource": "arn:aws:ecr:us-east-1:123456789012:repository/sagemaker-mlops"
    }]
  }'

# Create access keys
aws iam create-access-key --user-name github-actions
```

Save:
- `AccessKeyId`
- `SecretAccessKey`

### Step 3: Add AWS Credentials to GitHub Secrets

GitHub repo → Settings → Secrets and variables → Actions → New repository secret

```
AWS_ACCESS_KEY_ID = AccessKeyId from above
AWS_SECRET_ACCESS_KEY = SecretAccessKey from above
AWS_ACCOUNT_ID = 123456789012 (your account)
```

### Step 4: Push Workflow File

Workflow is already at: `.github/workflows/docker-build-push.yml`

Push it:
```bash
git add .github/workflows/
git commit -m "Add GitHub Actions CI/CD for Docker"
git push origin main
```

### Step 5: Test It!

Make a change to `Dockerfile` or training code:
```bash
# Any change to Dockerfile, training/, inference/, models/, or .github/
echo "# test" >> training/entry.py
git add training/entry.py
git commit -m "Trigger workflow"
git push origin main
```

Check GitHub → Actions tab → Watch workflow run ✅

---

## Understanding the Runner Machine

### What is "ubuntu-latest"?

```yaml
runs-on: ubuntu-latest  # ← GitHub-hosted, free runner
```

It's a **temporary Linux machine** that GitHub spins up for you:

```
Specs:
├─ OS: Ubuntu 24.04 (latest)
├─ CPU: 2 vCPU
├─ RAM: 7 GB
├─ Disk: 14 GB SSD
├─ Pre-installed: Docker, Python, AWS CLI, Git
└─ Cost: FREE (2000 min/month included)

Lifespan:
├─ Created when workflow starts
├─ Destroyed when workflow ends
└─ No persistent state

Location: GitHub data centers (you don't control where)
```

### Other Runner Options

```
runs-on: ubuntu-latest         # ← GitHub-hosted (free, recommended)
runs-on: macos-latest          # macOS for iOS builds
runs-on: windows-latest        # Windows
runs-on: [self-hosted, gpu]    # Your own EC2 machine with GPU (paid)
```

---

## How Credentials Are Used

### Flow

```
GitHub Secrets
    ├─ AWS_ACCESS_KEY_ID (encrypted in GitHub)
    ├─ AWS_SECRET_ACCESS_KEY (encrypted in GitHub)
    └─ AWS_ACCOUNT_ID
         ↓
Workflow reads secrets
         ↓
aws-actions/configure-aws-credentials@v4 (action)
         ↓
Sets AWS environment variables in runner:
    ├─ AWS_ACCESS_KEY_ID
    ├─ AWS_SECRET_ACCESS_KEY
    └─ AWS_DEFAULT_REGION
         ↓
aws-actions/amazon-ecr-login@v2 (action)
         ↓
docker login to ECR using those credentials
         ↓
docker push → ECR authorizes via credentials
```

### Security

- Secrets are **encrypted** in GitHub (can't see them in logs)
- Credentials are only injected into the runner (temporary machine)
- After workflow ends, machine is destroyed (credentials are gone)
- Best practice: Use minimal IAM permissions (ECR-only in this case)

---

## Workflow Triggers

Your workflow runs when:

```yaml
on:
  push:
    branches:
      - main          # Only pushes to main branch
    paths:
      - 'Dockerfile'  # AND any of these files change:
      - 'training/**'
      - 'inference/**'
      - 'models/**'
      - '.github/workflows/docker-build-push.yml'
  workflow_dispatch:  # Also: manual trigger via GitHub UI
```

**Examples:**
```
✅ WILL trigger:
   - Push Dockerfile change to main
   - Push training/entry.py change to main
   - Manual trigger via Actions tab

❌ WON'T trigger:
   - Push to branch other than main
   - Push change to README.md (not in paths)
   - Push to main but no relevant file changed
```

---

## What Gets Built

### Input
```
Your repo:
├─ Dockerfile         ← Defines image
├─ training/
├─ inference/
├─ models/
├─ requirements.txt
└─ pyproject.toml
```

### Build Process
```
docker build -t IMAGE_URI:COMMIT_SHA .
  ├─ Reads Dockerfile
  ├─ Installs dependencies (pip install ...)
  ├─ Copies code
  ├─ Sets entrypoint
  └─ Creates image (tagged with commit SHA)
```

### Output
```
Pushed to ECR:
├─ sagemaker-mlops:abc1234567890abcdef  (commit SHA)
└─ sagemaker-mlops:latest               (always latest)

Available at:
  123456789012.dkr.ecr.us-east-1.amazonaws.com/sagemaker-mlops
```

### Used By
```python
from agent import TrainingAgent

agent = TrainingAgent()
agent.train("xgbregressor")  # Uses:
                             # ECR_IMAGE_URI from sagemaker_config.py
                             # Which points to docker image built above ✅
```

---

## Real-World Example

### Scenario: You add GPU support to training

```bash
# 1. Modify training code
echo "import torch" >> training/entry.py

# 2. Update Dockerfile to include torch
# RUN pip install torch

# 3. Commit and push
git add training/entry.py Dockerfile
git commit -m "Add PyTorch GPU support"
git push origin main
```

### What Happens Automatically

```
1️⃣  GitHub detects push to main with Dockerfile change
2️⃣  Spins up ubuntu-latest runner (2 vCPU, 7GB RAM)
3️⃣  Checks out your code
4️⃣  Reads AWS credentials from GitHub Secrets
5️⃣  docker build -t image:commit_sha . 
    (installs torch, your code, dependencies)
6️⃣  docker push to ECR
7️⃣  Machine destroyed (workflow complete)
8️⃣  ✅ New image ready: sagemaker-mlops:latest
9️⃣  Next time you train, SageMaker pulls new image with PyTorch ✅
```

No manual steps. No docker build locally. No pushing manually.

---

## Cost Breakdown

| Item | Cost |
|------|------|
| GitHub-hosted runner (2000 min/month) | FREE ✅ |
| ECR storage (< 10 images) | ~$0.10/month |
| Data transfer (push to ECR) | ~$0.01/month |
| **Total** | **~$0.11/month** |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Workflow doesn't start | Check `paths:` matches your change, or use `workflow_dispatch` (manual) |
| Build fails: "AWS credentials not configured" | Add AWS secrets to GitHub (Settings → Secrets) |
| Build fails: "repository does not exist" | Create ECR repo: `aws ecr create-repository --repository-name sagemaker-mlops` |
| Build takes > 5 min | Normal for first build (installs dependencies). Subsequent builds use cache. |
| Image not in ECR after workflow | Check Actions tab for error logs. Most common: missing credentials or wrong policy. |

---

## Next Steps

1. **Setup** (one-time):
   - Create ECR repo
   - Create IAM user + credentials
   - Add credentials to GitHub Secrets
   - Verify workflow file at `.github/workflows/docker-build-push.yml`

2. **Test**:
   - Make dummy change to Dockerfile
   - Push to main
   - Check Actions tab → workflow runs ✅
   - Verify image appears in ECR

3. **Use**:
   - Make real code changes
   - Workflow builds automatically
   - Use image in SageMaker training

---

## See Also

- [Full Setup Guide](workflows/SETUP.md)
- [Workflow File](docker-build-push.yml)
- [SageMaker Config](../1_sagemaker-mlops/sagemaker_config.py)
