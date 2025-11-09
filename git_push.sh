#!/bin/bash
# Git setup and push script for West Bengal Electoral Data repository
# Repository: https://github.com/partha-dhar/wb-electoral-data

echo "=================================================="
echo "Git Setup and Push Script"
echo "=================================================="
echo ""

# Check git configuration
echo "Checking Git configuration..."
GIT_USER=$(git config --global user.name)
GIT_EMAIL=$(git config --global user.email)

if [ -z "$GIT_USER" ] || [ -z "$GIT_EMAIL" ]; then
    echo "❌ Git user not configured globally!"
    echo "Please run:"
    echo "  git config --global user.name 'Your Name'"
    echo "  git config --global user.email 'your.email@example.com'"
    exit 1
else
    echo "✅ Git user: $GIT_USER <$GIT_EMAIL>"
fi

echo ""
echo "=================================================="
echo "Step 1: Initialize Git repository"
echo "=================================================="
git init
if [ $? -ne 0 ]; then
    echo "❌ Failed to initialize git repository"
    exit 1
fi
echo "✅ Git repository initialized"

echo ""
echo "=================================================="
echo "Step 2: Add all files"
echo "=================================================="
git add .
if [ $? -ne 0 ]; then
    echo "❌ Failed to add files"
    exit 1
fi
echo "✅ All files staged"

echo ""
echo "=================================================="
echo "Step 3: Create commit with message"
echo "=================================================="
git commit -F COMMIT_MESSAGE.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to create commit"
    exit 1
fi
echo "✅ Commit created successfully"

echo ""
echo "=================================================="
echo "Step 4: Rename branch to main"
echo "=================================================="
git branch -M main
if [ $? -ne 0 ]; then
    echo "❌ Failed to rename branch"
    exit 1
fi
echo "✅ Branch renamed to main"

echo ""
echo "=================================================="
echo "Step 5: Add remote origin"
echo "=================================================="
git remote add origin https://github.com/partha-dhar/wb-electoral-data.git
if [ $? -ne 0 ]; then
    echo "⚠️  Remote might already exist, removing and re-adding..."
    git remote remove origin
    git remote add origin https://github.com/partha-dhar/wb-electoral-data.git
fi
echo "✅ Remote origin added"

echo ""
echo "=================================================="
echo "Step 6: Push to GitHub"
echo "=================================================="
echo "Pushing to: https://github.com/partha-dhar/wb-electoral-data"
echo ""
git push -u origin main
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Failed to push to GitHub"
    echo ""
    echo "If you need to force push (use with caution):"
    echo "  git push -u origin main --force"
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ SUCCESS! Repository pushed to GitHub"
echo "=================================================="
echo ""
echo "Repository URL: https://github.com/partha-dhar/wb-electoral-data"
echo ""
echo "Next steps:"
echo "1. Visit your repository on GitHub"
echo "2. Update repository description and topics"
echo "3. Enable Issues and Discussions"
echo "4. Create first release (v1.0.0)"
echo "5. Star your repository ⭐"
echo ""
echo "Files committed:"
git log -1 --stat
echo ""
echo "=================================================="
