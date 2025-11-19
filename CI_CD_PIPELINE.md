# CI/CD Pipeline Documentation

## Overview

This project includes a comprehensive CI/CD (Continuous Integration/Continuous Deployment) pipeline using GitHub Actions.

## Pipeline Workflows

### 1. **CI Pipeline** (`ci.yml`)
Runs on every push and pull request to test code quality and functionality.

#### Jobs:
- **Backend Tests** (Multi-version)
  - Python 3.8, 3.9, 3.10, 3.11
  - Code linting (flake8)
  - Code formatting check (black)
  - Type checking (mypy)
  - Unit tests with coverage
  - Coverage upload to Codecov

- **Frontend Tests** (Multi-version)
  - Node 18.x, 20.x
  - ESLint & code quality
  - Unit tests (Vitest)
  - Build verification
  - Coverage upload to Codecov

- **Security Scanning**
  - Bandit security analysis
  - Dependency vulnerability checks (safety)

- **Code Quality**
  - Complexity analysis (Radon)
  - Code linting (Pylint)

- **Dependency Check**
  - Verify all dependencies can be installed

#### Trigger:
- On push to `main`, `develop`, or feature branches
- On pull requests to `main` or `develop`
- Weekly scheduled runs

#### Status Badge:
```markdown
[![CI](https://github.com/Krupa537/Attrition_analysis_system/actions/workflows/ci.yml/badge.svg)](https://github.com/Krupa537/Attrition_analysis_system/actions/workflows/ci.yml)
```

---

### 2. **CD Pipeline** (`cd.yml`)
Deploys code to staging and production environments.

#### Jobs:
- **Build Docker Images**
  - Backend service
  - Frontend service
  - Push to Docker registry
  - Metadata tagging (branch, semver, SHA)
  - Layer caching for faster builds

- **Deploy to Staging**
  - Triggered on `develop` branch
  - SSH deployment to staging server
  - Docker Compose orchestration

- **Deploy to Production**
  - Triggered on `main` branch
  - GitHub deployment tracking
  - SSH deployment to production
  - Health checks (30 retries with 10s timeout)
  - Slack notifications

- **Rollback on Failure**
  - Automatic rollback if deployment fails
  - Reverts to previous commit
  - Slack alert

#### Required Secrets:
```
DOCKER_USERNAME          # Docker Hub username
DOCKER_PASSWORD          # Docker Hub access token
DOCKER_REGISTRY          # Docker registry URL
STAGING_HOST            # Staging server hostname
STAGING_USER            # Staging SSH user
STAGING_SSH_KEY         # Staging SSH private key
PROD_HOST               # Production server hostname
PROD_USER               # Production SSH user
PROD_SSH_KEY            # Production SSH private key
SLACK_WEBHOOK           # Slack webhook for notifications
```

#### Trigger:
- On push to `main` branch
- On git tags (`v*`)
- Manual trigger via `workflow_dispatch`

---

### 3. **PR Quality Checks** (`pr-quality.yml`)
Enhanced quality checks specifically for pull requests.

#### Jobs:
- **PR Quality**
  - Python formatting check (black)
  - Python linting (flake8)
  - Backend tests
  - Frontend tests
  - Build verification

- **Size Check**
  - Bundle size analysis
  - Diff size warnings (alerts if >1000 lines)
  - Compressed size reporting

- **Documentation Check**
  - Warns if code changed without doc updates
  - Posts helpful comment on PR

#### Trigger:
- On pull request events (`opened`, `synchronize`, `reopened`, `ready_for_review`)

---

## Setup Instructions

### Step 1: Add GitHub Secrets
Go to **Settings > Secrets and variables > Actions** and add:

```bash
DOCKER_USERNAME=your-docker-username
DOCKER_PASSWORD=your-docker-token
DOCKER_REGISTRY=docker.io
STAGING_HOST=staging.example.com
STAGING_USER=deploy
STAGING_SSH_KEY=$(cat ~/.ssh/staging_key)
PROD_HOST=production.example.com
PROD_USER=deploy
PROD_SSH_KEY=$(cat ~/.ssh/prod_key)
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Step 2: Configure Docker Hub
1. Create Docker Hub account at https://hub.docker.com
2. Generate access token in Settings
3. Add `DOCKER_USERNAME` and `DOCKER_PASSWORD` to GitHub Secrets

### Step 3: Setup SSH Keys
Generate SSH keys for deployment:
```bash
ssh-keygen -t ed25519 -f ~/.ssh/staging_key
ssh-keygen -t ed25519 -f ~/.ssh/prod_key

# Add public keys to server ~/.ssh/authorized_keys
ssh-copy-id -i ~/.ssh/staging_key.pub user@staging.example.com
ssh-copy-id -i ~/.ssh/prod_key.pub user@production.example.com
```

### Step 4: Configure Docker Compose
Update `docker-compose.yml` with your environment variables and endpoints.

### Step 5: Add Health Check Endpoint
Ensure backend has a `/health` endpoint:
```python
@app.get('/health')
async def health():
    return {'status': 'healthy'}
```

---

## Pipeline Flow

```
┌─────────────┐
│   Push/PR   │
└──────┬──────┘
       │
       ├─────────────────────────────────────────┐
       │                                         │
    ┌──▼─────┐                             ┌────▼──────┐
    │ CI Job │                             │ PR Quality│
    └──┬─────┘                             └────┬──────┘
       │                                        │
       ├─ Backend Tests                        ├─ Code Formatting
       ├─ Frontend Tests                       ├─ Linting
       ├─ Security Scan                        ├─ Tests
       ├─ Code Quality                         ├─ Build Check
       └─ Dependencies                         └─ Size Check
           │                                        │
           └────────────────────┬────────────────────┘
                                │
                         ┌──────▼──────┐
                         │ All Checks  │
                         │   Passed?   │
                         └──────┬──────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                  YES                      NO
                    │                       │
            ┌───────▼────────┐     ┌──────▼──────┐
            │ On Main/Tags?  │     │  Block PR   │
            └───────┬────────┘     └─────────────┘
                    │
           ┌────────┴────────┐
           │                 │
         YES                NO
           │                 │
    ┌──────▼────────┐  ┌────▼──────────┐
    │ Build Docker  │  │ Skip Deploy   │
    │   Images      │  └───────────────┘
    └──────┬────────┘
           │
    ┌──────▼──────┐
    │  On Develop? │
    └──────┬──────┘
           │
      ┌────┴───────┐
      │             │
    YES            NO
      │             │
   ┌──▼──────┐   ┌─▼────────────┐
   │ Staging │   │ Production   │
   │ Deploy  │   │ Deploy       │
   └──┬──────┘   └─┬────────────┘
      │           │
  ┌───▼────┐  ┌───▼────┐
  │ Healthy?   │Healthy?
  └───┬────┘  └───┬────┘
      │           │
  ┌───▴───┐   ┌───▴───┐
  │ Pass  │   │Rollback│
  └───────┘   └────┬───┘
                  │
            ┌─────▼──────┐
            │ Slack Alert│
            └────────────┘
```

---

## Local Development

### Run CI Locally
```bash
# Install act (GitHub Actions runner)
brew install act  # macOS
# or download from https://github.com/nektos/act

# Run specific workflow
act -j backend-tests
act -j frontend-tests

# Run all CI jobs
act push
```

### Docker Build Locally
```bash
# Build backend
docker build -t attrition-backend:latest ./backend

# Build frontend
docker build -t attrition-frontend:latest ./frontend

# Run with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f
```

---

## Monitoring & Alerts

### GitHub Actions Dashboard
- View all workflow runs: **Actions** tab in repository
- Check individual job logs: Click on workflow run

### Coverage Reports
- View on Codecov: https://codecov.io/gh/Krupa537/Attrition_analysis_system
- Inline coverage comments on PRs

### Slack Notifications
Receives notifications for:
- Production deployments
- Failed deployments
- Rollbacks

### Health Checks
- Backend: `GET /health` (30s interval, 3 retries)
- Frontend: HTTP 200 response (30s interval, 3 retries)

---

## Best Practices

### 1. Branch Strategy
```
main (production)
  ├─ Protected branch
  └─ Requires PR with CI passing

develop (staging)
  ├─ Staging deployments
  └─ Feature branch source

feature/* (development)
  ├─ Feature branches
  └─ Must have PR to develop
```

### 2. Commit Messages
Use conventional commits:
```
feat: Add at-risk employee identification
fix: Correct login redirect
docs: Update README
test: Add coverage for auth module
```

### 3. PR Guidelines
- Keep PRs small (<1000 line changes)
- Update documentation with code changes
- Ensure all CI checks pass
- Request review before merge

### 4. Secrets Management
- Never commit secrets to repository
- Use GitHub Secrets for sensitive data
- Rotate SSH keys periodically
- Restrict secret access to required workflows

---

## Troubleshooting

### Workflow Failures

**Backend tests failing:**
```bash
# Run locally
cd backend
pytest tests/ -v
python -m flake8 app/
```

**Frontend tests failing:**
```bash
# Run locally
cd frontend
npm test -- --run
npm run build
```

**Docker build failing:**
- Check Dockerfile syntax
- Verify all dependencies in requirements.txt
- Check build context paths

**Deployment failing:**
- Verify SSH keys are correctly configured
- Check server connectivity: `ssh -i key user@host`
- Review docker-compose.yml configuration
- Check health check endpoint

### Debug Workflow
Add debug step to workflow:
```yaml
- name: Debug info
  run: |
    echo "Ref: ${{ github.ref }}"
    echo "SHA: ${{ github.sha }}"
    echo "Actor: ${{ github.actor }}"
    docker version
    python --version
```

---

## Advanced Configuration

### Matrix Builds
Automatically test multiple configurations:
```yaml
strategy:
  matrix:
    python-version: ['3.8', '3.9', '3.10', '3.11']
```

### Conditional Steps
Only run on specific branches:
```yaml
if: github.ref == 'refs/heads/main'
```

### Caching
Speed up builds with caching:
```yaml
- uses: actions/setup-python@v4
  with:
    cache: 'pip'
```

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

## Support

For issues or questions about the CI/CD pipeline:
1. Check workflow logs in GitHub Actions
2. Review troubleshooting section above
3. Check individual test output
4. Review CI configuration files

---

**Last Updated:** 2025-11-18  
**Pipeline Status:** ✅ Ready for Production
