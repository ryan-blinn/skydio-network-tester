# GitHub Setup Guide

## 📋 Pre-Export Checklist

Before pushing to GitHub, ensure you've completed these steps:

### ✅ Step 1: Review Sensitive Files

**Files to NEVER commit** (already in .gitignore):
- `config.json` - Contains API tokens and credentials
- `test_history/` - Contains user test data
- `exports/` - Contains generated reports
- Any `.key`, `.pem`, `.token` files

**Safe to commit**:
- `config.example.json` - Template configuration
- All source code files
- Documentation files
- Static assets (CSS, JS, images)

### ✅ Step 2: Initialize Git (Already Done)

The repository has been initialized. Now let's configure it:

```bash
cd /Users/ryan.blinn/CascadeProjects/windsurf-project

# Set your Git identity (if not already set globally)
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### ✅ Step 3: Stage Files

```bash
# Add all files (respecting .gitignore)
git add .

# Check what will be committed
git status
```

### ✅ Step 4: Create Initial Commit

```bash
git commit -m "Initial commit: Skydio Network Readiness Tester

- Complete network testing suite (DNS, TCP, QUIC, Ping, NTP, Speed)
- Modern web interface with test history
- Export functionality (PDF, CSV, JSON)
- Databricks and webhook integrations
- Raspberry Pi optimized
- Private IP display with Raspberry Pi icon"
```

---

## 🌐 Create GitHub Repository

### Option A: Using GitHub Web Interface

1. **Go to GitHub**: https://github.com/new

2. **Repository Settings**:
   - **Name**: `skydio-network-tester` (or your preferred name)
   - **Description**: "Network readiness testing tool for Skydio drone operations"
   - **Visibility**: 
     - ⚠️ **Private** (recommended - contains proprietary code)
     - Public (only if approved by Skydio)
   - **Initialize**: 
     - ❌ Do NOT add README (we already have one)
     - ❌ Do NOT add .gitignore (we already have one)
     - ❌ Do NOT add license

3. **Click "Create repository"**

4. **Copy the repository URL** (shown on the next page):
   - HTTPS: `https://github.com/username/skydio-network-tester.git`
   - SSH: `git@github.com:username/skydio-network-tester.git`

---

### Option B: Using GitHub CLI (gh)

```bash
# Install GitHub CLI if not already installed
# macOS: brew install gh
# Login to GitHub
gh auth login

# Create private repository
gh repo create skydio-network-tester --private --source=. --remote=origin --push

# Or create public repository (if approved)
gh repo create skydio-network-tester --public --source=. --remote=origin --push
```

---

## 🚀 Push to GitHub

### If you created the repo via Web Interface:

```bash
# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/skydio-network-tester.git

# Or use SSH (if you have SSH keys set up)
git remote add origin git@github.com:YOUR_USERNAME/skydio-network-tester.git

# Verify remote
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

### If you used GitHub CLI:

The repository is already pushed! You're done! 🎉

---

## 📝 Post-Upload Tasks

### 1. Add Repository Description

On GitHub, go to your repository and click "About" (gear icon) to add:
- **Description**: "Network readiness testing tool for Skydio drone operations"
- **Topics**: `skydio`, `network-testing`, `raspberry-pi`, `flask`, `python`
- **Website**: (if you have a demo site)

### 2. Create Repository Sections

GitHub will automatically detect:
- ✅ README.md
- ✅ LICENSE (if you add one)
- ✅ .gitignore

### 3. Set Up Branch Protection (Optional)

For team projects:
1. Go to Settings → Branches
2. Add rule for `main` branch
3. Enable:
   - Require pull request reviews
   - Require status checks to pass
   - Require branches to be up to date

### 4. Add Collaborators (If Needed)

1. Go to Settings → Collaborators
2. Add team members with appropriate permissions

---

## 🔒 Security Best Practices

### 1. Verify No Secrets Were Committed

```bash
# Search for potential secrets
git log --all --full-history --source --oneline -- config.json
git log --all --full-history --source --oneline -- "*.key"
git log --all --full-history --source --oneline -- "*.token"

# If you find secrets, see "Remove Secrets" section below
```

### 2. Add GitHub Secret Scanning

GitHub automatically scans for common secrets. Enable additional protection:
1. Go to Settings → Code security and analysis
2. Enable:
   - Dependency graph
   - Dependabot alerts
   - Dependabot security updates
   - Secret scanning

### 3. Add Security Policy

Create `SECURITY.md`:
```markdown
# Security Policy

## Reporting a Vulnerability

Please report security vulnerabilities to: security@skydio.com

Do not open public issues for security vulnerabilities.
```

---

## 🚨 Emergency: Remove Committed Secrets

If you accidentally committed sensitive data:

### Option 1: Remove from Last Commit (Not Yet Pushed)

```bash
# Remove file from staging
git rm --cached config.json

# Amend the commit
git commit --amend --no-edit

# Force push (if already pushed)
git push --force
```

### Option 2: Remove from History (BFG Repo-Cleaner)

```bash
# Install BFG
brew install bfg

# Clone a fresh copy
git clone --mirror https://github.com/YOUR_USERNAME/skydio-network-tester.git

# Remove sensitive file from all history
bfg --delete-files config.json skydio-network-tester.git

# Clean up
cd skydio-network-tester.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push --force
```

### Option 3: Rotate All Credentials

If secrets were exposed:
1. ✅ Rotate all API tokens immediately
2. ✅ Change all passwords
3. ✅ Revoke Databricks access tokens
4. ✅ Update webhook URLs/tokens
5. ✅ Notify security team

---

## 📦 Ongoing Maintenance

### Regular Updates

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add feature: XYZ"

# Push to GitHub
git push origin main
```

### Create Feature Branches

```bash
# Create and switch to new branch
git checkout -b feature/new-test-type

# Make changes and commit
git add .
git commit -m "Add new test type"

# Push branch
git push origin feature/new-test-type

# Create pull request on GitHub
```

### Tagging Releases

```bash
# Create annotated tag
git tag -a v2.0.0 -m "Version 2.0.0: Added test history and private IP display"

# Push tags
git push origin --tags
```

---

## 📊 Repository Structure on GitHub

After upload, your repository will look like:

```
skydio-network-tester/
├── .github/
│   └── workflows/          # (Optional) CI/CD workflows
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── templates/
├── systemd/
├── .gitignore
├── README.md
├── PROJECT_DOCUMENTATION.md
├── README_COMPREHENSIVE.md
├── GITHUB_SETUP.md
├── config.example.json     # Safe template
├── requirements.txt
├── app.py
├── network_tests.py
├── report_export.py
├── databricks_integration.py
├── excel_config_parser.py
└── auto_network_tester.py
```

**NOT included** (in .gitignore):
- ❌ config.json
- ❌ test_history/
- ❌ exports/
- ❌ __pycache__/
- ❌ *.pyc

---

## 🔗 Useful Git Commands

### Check Status
```bash
git status                    # See what's changed
git log --oneline            # View commit history
git diff                     # See unstaged changes
```

### Undo Changes
```bash
git checkout -- file.py      # Discard changes to file
git reset HEAD file.py       # Unstage file
git reset --soft HEAD~1      # Undo last commit (keep changes)
git reset --hard HEAD~1      # Undo last commit (discard changes)
```

### Sync with GitHub
```bash
git fetch origin             # Download changes
git pull origin main         # Download and merge changes
git push origin main         # Upload your changes
```

### Branching
```bash
git branch                   # List branches
git branch feature-name      # Create branch
git checkout feature-name    # Switch to branch
git checkout -b feature-name # Create and switch
git merge feature-name       # Merge branch into current
git branch -d feature-name   # Delete branch
```

---

## 🎯 Next Steps

1. ✅ **Verify Upload**: Visit your GitHub repository URL
2. ✅ **Test Clone**: Clone to a different location and verify it works
3. ✅ **Update Documentation**: Add any project-specific notes
4. ✅ **Set Up CI/CD**: (Optional) Add GitHub Actions for testing
5. ✅ **Share with Team**: Add collaborators if needed

---

## 📞 Need Help?

- **Git Documentation**: https://git-scm.com/doc
- **GitHub Guides**: https://guides.github.com/
- **GitHub CLI**: https://cli.github.com/manual/

---

**Ready to push to GitHub!** 🚀

Run the commands in the "Push to GitHub" section above to complete the upload.
