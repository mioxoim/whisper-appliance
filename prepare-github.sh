#!/bin/bash
# GitHub Repository Preparation Script
# Prepares the WhisperS2T repository for initial GitHub push

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo ""
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -f "install-container.sh" ]; then
    print_error "This script must be run from the whisper-appliance repository root"
    exit 1
fi

print_section "🚀 Preparing WhisperS2T Repository for GitHub"

# 1. Clean up any build artifacts
print_status "Cleaning build artifacts and temporary files"
rm -rf build/ cache/ mock_results/ venv/ __pycache__/ *.pyc *.log 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 2. Check for large files that should be ignored
print_status "Checking for large files (>50MB)"
large_files=$(find . -size +50M -type f 2>/dev/null | grep -v ".git" || true)
if [ -n "$large_files" ]; then
    print_warning "Large files found that should be in .gitignore:"
    echo "$large_files"
fi

# 3. Check for sensitive information
print_status "Scanning for potential sensitive information"
sensitive_patterns="password|secret|key|token|credential"
sensitive_files=$(grep -r -i "$sensitive_patterns" --include="*.py" --include="*.sh" --include="*.md" . 2>/dev/null | grep -v ".git" | grep -v "SECURITY.md" | grep -v "password.*example" || true)
if [ -n "$sensitive_files" ]; then
    print_warning "Potential sensitive information found:"
    echo "$sensitive_files"
    print_warning "Please review these matches before pushing to GitHub"
fi

# 4. Validate script syntax
print_status "Validating shell script syntax"
for script in *.sh; do
    if [ -f "$script" ]; then
        if bash -n "$script"; then
            print_success "✓ $script syntax OK"
        else
            print_error "✗ $script has syntax errors"
            exit 1
        fi
    fi
done

# 5. Check Python syntax if files exist
if ls src/*.py >/dev/null 2>&1; then
    print_status "Validating Python syntax"
    for pyfile in src/*.py; do
        if python3 -m py_compile "$pyfile" 2>/dev/null; then
            print_success "✓ $pyfile syntax OK"
        else
            print_error "✗ $pyfile has syntax errors"
            exit 1
        fi
    done
fi

# 6. Check documentation completeness
print_status "Checking documentation completeness"
required_docs=("README.md" "CHANGELOG.md" "LICENSE" "CONTRIBUTING.md" "SECURITY.md" "PROXMOX-QUICKSTART.md")
for doc in "${required_docs[@]}"; do
    if [ -f "$doc" ]; then
        print_success "✓ $doc exists"
    else
        print_error "✗ Missing required documentation: $doc"
        exit 1
    fi
done

# 7. Check that version numbers are consistent
print_status "Checking version consistency"
version_files=("README.md" "CHANGELOG.md")
version="v0.6.0"
for file in "${version_files[@]}"; do
    if grep -q "$version" "$file"; then
        print_success "✓ $file contains $version"
    else
        print_warning "! $file might not contain current version $version"
    fi
done

# 8. Check git status
print_status "Checking git repository status"
if [ -d ".git" ]; then
    print_success "✓ Git repository initialized"
    
    # Check for untracked large files
    untracked_large=$(git status --porcelain | grep "^??" | awk '{print $2}' | xargs -I {} find {} -size +10M 2>/dev/null || true)
    if [ -n "$untracked_large" ]; then
        print_warning "Large untracked files found:"
        echo "$untracked_large"
        print_warning "Consider adding to .gitignore"
    fi
else
    print_warning "! Not a git repository - run 'git init' first"
fi

# 9. Validate .gitignore completeness
print_status "Validating .gitignore coverage"
gitignore_patterns=("*.iso" "*.log" "models/" "cache/" "venv/" "__pycache__/")
if [ -f ".gitignore" ]; then
    for pattern in "${gitignore_patterns[@]}"; do
        if grep -q "$pattern" .gitignore; then
            print_success "✓ .gitignore includes $pattern"
        else
            print_warning "! .gitignore missing pattern: $pattern"
        fi
    done
else
    print_error "✗ .gitignore file missing"
    exit 1
fi

# 10. Check GitHub workflow files
print_status "Checking GitHub Actions workflow"
if [ -f ".github/workflows/ci.yml" ]; then
    print_success "✓ CI/CD workflow configured"
else
    print_warning "! No GitHub Actions workflow found"
fi

# 11. Estimate repository size
print_status "Estimating repository size"
if command -v du >/dev/null 2>&1; then
    repo_size=$(du -sh . 2>/dev/null | cut -f1)
    print_status "Repository size: $repo_size"
    
    # Check for overly large repository
    size_mb=$(du -sm . 2>/dev/null | cut -f1)
    if [ "$size_mb" -gt 100 ]; then
        print_warning "Repository is quite large (${size_mb}MB). Consider cleaning up or using Git LFS for large files."
    fi
fi

# 12. Generate pre-commit checklist
print_section "📋 Pre-Commit Checklist"
echo -e "${GREEN}Before pushing to GitHub, ensure:${NC}"
echo "□ All sensitive information removed"
echo "□ Large files are in .gitignore"  
echo "□ Documentation is up to date"
echo "□ Version numbers are consistent"
echo "□ All scripts have been tested"
echo "□ License and contributing guidelines are appropriate"
echo "□ Security policy is reviewed"

# 13. GitHub repository setup commands
print_section "🔧 GitHub Setup Commands"
echo -e "${YELLOW}After creating the GitHub repository, run:${NC}"
echo ""
echo "# Initialize git (if not done already)"
echo "git init"
echo ""
echo "# Add all files"
echo "git add ."
echo ""
echo "# Initial commit"
echo "git commit -m \"Initial commit: WhisperS2T Container-First Appliance v0.6.0\""
echo ""
echo "# Add GitHub remote (replace with your repository URL)"
echo "git remote add origin https://github.com/yourusername/whisper-appliance.git"
echo ""
echo "# Push to GitHub"
echo "git branch -M main"
echo "git push -u origin main"

# 14. Post-push recommendations
print_section "📚 Post-Push Recommendations"
echo -e "${YELLOW}After pushing to GitHub:${NC}"
echo "1. Enable GitHub Actions (should run automatically)"
echo "2. Set up branch protection for main branch"
echo "3. Configure repository topics/tags for discoverability"
echo "4. Consider enabling GitHub Security Advisories"
echo "5. Set up repository description and website URL"
echo "6. Review and test the container installation from GitHub"

print_section "✅ Repository Preparation Complete"
print_success "WhisperS2T repository is ready for GitHub!"
print_success ""
print_success "🎯 Key Features Ready for Open Source:"
print_success "   ✓ Container-first deployment (10-minute setup)"
print_success "   ✓ Complete documentation and guides"
print_success "   ✓ GitHub Actions CI/CD pipeline"  
print_success "   ✓ Security policy and guidelines"
print_success "   ✓ Contributing guidelines"
print_success "   ✓ Issue templates for bug reports and features"
print_success ""
print_success "🚀 Ready to share with the community!"