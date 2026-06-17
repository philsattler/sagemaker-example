# Docker Build Setup

## Overview

The Docker build process uses two dependency sources to work correctly:

```
pyproject.toml  ←  Your source of truth (maintains dependencies)
       ↓
requirements.txt  ←  Generated for Docker (pip understands this)
       ↓
Dockerfile  ←  Uses requirements.txt to build image
```

---

## Files and Their Purposes

### `Dockerfile` (Root)
- **Single source** of truth for building Docker images
- Used by:
  - GitHub Actions CI/CD pipeline (builds and pushes to ECR)
  - Local `docker build` commands
  - SageMaker training jobs
- Copies code from `1_sagemaker-mlops/` subdirectory (respects project organization)
- Uses `requirements.txt` for dependency installation

### `pyproject.toml`
- **Your project's dependency source**
- Defines all Python packages needed
- Used for local development with `uv`
- NOT understood by Docker's `pip install` command
- When you add/remove dependencies, update this file

### `requirements.txt`
- **Generated dependency list** for Docker
- Created from `pyproject.toml`
- Only used during Docker builds
- Should be regenerated whenever `pyproject.toml` changes
- Format: `package==version` (pip understands this)

### `docker/entrypoint.sh`
- **Container entry point** script
- Routes between training and inference based on `PHASE` environment variable
- Referenced in Dockerfile: `COPY docker/entrypoint.sh /opt/ml/code/entrypoint.sh`
- Still needed, not deleted

---

## Why Two Files? (pyproject.toml vs requirements.txt)

### Local Development
```bash
# You use uv (understands pyproject.toml)
uv pip install
uv pip add numpy
```

### Docker Build
```dockerfile
# Docker only understands pip with requirements.txt
RUN pip install -r requirements.txt
```

**Why not put requirements.txt directly in pyproject.toml?**
- Docker's `pip install` doesn't understand `pyproject.toml`
- Docker is a 10+ year old ecosystem, uses older tooling
- Modern Python tools (uv, poetry, pipenv) generate `requirements.txt` from project config
- This is standard practice in the industry

---

## When to Update Dependencies

### Adding a new package
1. Update `pyproject.toml` with the new package
2. Regenerate `requirements.txt`:
   ```bash
   # If using pip-tools
   pip-compile pyproject.toml -o requirements.txt
   
   # Or manually sync
   uv pip install package-name
   uv pip freeze > requirements.txt
   ```
3. Commit both files
4. Next GitHub Actions run will build new Docker image with new dependency

### Current Setup
For this project, `requirements.txt` was manually created from `pyproject.toml` with:
```python
[project]
dependencies = [
    "boto3==1.34.0",
    "sagemaker==2.224.4",
    ...
]
```

→ Created `requirements.txt` with those same versions

---

## Docker Build Workflow

```
You push code to GitHub
  ↓
GitHub Actions detects push to 1_sagemaker-mlops/ or Dockerfile
  ↓
Workflow runs on ubuntu-latest runner
  ↓
docker build -t image:tag .
  ├─ Reads Dockerfile
  ├─ Copies requirements.txt
  ├─ RUN pip install -r requirements.txt
  ├─ Copies code from 1_sagemaker-mlops/
  ├─ Copies docker/entrypoint.sh
  └─ Image ready
  ↓
docker push to ECR
  ↓
SageMaker training pulls image from ECR
```

---

## Common Questions

**Q: Do I need to update requirements.txt manually?**  
A: Only if you change `pyproject.toml`. Keep them in sync.

**Q: Can I use uv inside Docker?**  
A: Technically yes, but `pip` is standard in Docker. Stick with `pip install -r requirements.txt`.

**Q: What if requirements.txt and pyproject.toml disagree?**  
A: Update both to match. Docker builds use `requirements.txt`, so that's what matters for training.

**Q: Why keep docker/entrypoint.sh but delete docker/Dockerfile?**  
A: `entrypoint.sh` routes between training/inference phases. `Dockerfile` was just an old copy at wrong location.

**Q: Can I move entrypoint.sh to root?**  
A: Yes, but `docker/` is a logical place for Docker-specific files. Keep it there.

---

## File Structure (After Cleanup)

```
sagemaker-example/
├── Dockerfile                 ← Single source, used by GitHub Actions & SageMaker
├── pyproject.toml             ← Your dependency source
├── requirements.txt           ← Generated for Docker (pip format)
├── 1_sagemaker-mlops/
│   ├── training/
│   ├── inference/
│   ├── models/
│   └── sagemaker_config.py
└── docker/
    └── entrypoint.sh          ← Container routing logic
```

---

## See Also

- [GitHub Actions CI/CD](/.github/workflows/docker-build-push.yml)
- [Training Metrics](1_sagemaker-mlops/METRICS_LOGGING.md)
- [SageMaker MLOps](1_sagemaker-mlops/README.md)
