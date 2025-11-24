# Git Branching Strategy for Client Development

**Date**: November 23, 2025  
**Status**: Dev branch created and active

---

## Overview

When developing software for a client with regular reviews, you need to manage:
- **Stable versions** for client demos
- **Work-in-progress** development
- **Easy rollback** to previous versions
- **Professional presentation** (no broken/incomplete features shown)

**Solution**: Use Git branches to maintain parallel versions of your code.

---

## What Are Branches?

**Branches are parallel versions of your code** - separate timelines that exist simultaneously.

Think of it like:
- Main road = `main` branch (stable, always works)
- Side street = `dev` branch (your workshop, can be messy)
- Driveways = `feature` branches (individual features)

You can switch between them instantly without losing work.

---

## Your Branching Strategy

### **"Main = Stable, Dev = Work in Progress"**

```
main branch    (stable, client-ready versions)
  │
  │ v1.0 ────── v1.1 ────── v1.2 (tagged releases)
  │
  │
dev branch     (your active development)
  │
  ├─ feature/rbac
  ├─ feature/theme-toggle
  └─ feature/reports
```

### Branch Purposes:

1. **`main` branch** = Production-ready, stable code
   - Only merge here when features are complete and tested
   - This is what you show clients
   - Tag releases: `v1.0`, `v1.1`, `v2.0`, etc.
   - **Always deployable**

2. **`dev` branch** = Your daily work
   - All your active development happens here
   - Can be messy, experimental, incomplete
   - Client never sees this
   - **Your sandbox**

3. **Feature branches** (optional) = Individual features
   - `feature/rbac-system`
   - `feature/financial-reports`
   - Merge into `dev` when done
   - Then `dev` → `main` when ready for client

---

## Daily Development Workflow

### Your Regular Work:

```powershell
# Make sure you're on dev branch
git checkout dev

# Work on your code
# ... edit files ...

# Commit your changes
git add .
git commit -m "Implemented RBAC permission checks"

# Push to GitHub (backup + sync across computers)
git push origin dev
```

### Check Which Branch You're On:

```powershell
git branch
# The one with * is your current branch
```

---

## Preparing for Client Review

### When Features Are Ready for Demo:

```powershell
# 1. Make sure dev branch is clean
git checkout dev
git status  # Should show no uncommitted changes

# 2. Switch to main branch
git checkout main

# 3. Merge stable features from dev
git merge dev

# 4. Tag this version
git tag v1.1

# 5. Push to GitHub
git push origin main --tags

# 6. Build executable from main
# (Run your build script/process here)

# 7. Switch back to dev to continue work
git checkout dev
```

### Show Client a Specific Version:

```powershell
# Checkout a specific tag
git checkout v1.0

# Build executable
# Present to client

# Return to current work
git checkout dev
```

---

## Working Across Multiple Computers

### On Computer A:
```powershell
# Do some work
git checkout dev
# ... make changes ...
git add .
git commit -m "Added new feature"
git push origin dev
```

### On Computer B:
```powershell
# Get latest changes
git checkout dev
git pull origin dev

# Continue working
# ... make changes ...
git add .
git commit -m "Fixed bug in feature"
git push origin dev
```

**Key Point**: Always `git pull` before starting work to get latest changes!

---

## Essential Commands Reference

### Checking Status:
```powershell
git status              # See what's changed
git branch              # List branches (* = current)
git branch -a           # List all branches (including remote)
git log --oneline       # See commit history
```

### Switching Branches:
```powershell
git checkout branch-name       # Switch to existing branch
git checkout -b new-branch     # Create AND switch to new branch
```

### Creating Branches:
```powershell
git checkout -b feature/rbac   # Create feature branch from current
git push -u origin feature/rbac # Push to GitHub
```

### Merging:
```powershell
git checkout main              # Switch to destination branch
git merge dev                  # Merge dev INTO main
```

### Tagging Releases:
```powershell
git tag v1.0                   # Create tag at current commit
git tag -a v1.0 -m "First client demo"  # Tag with message
git push origin v1.0           # Push single tag
git push origin --tags         # Push all tags
git tag                        # List all tags
```

### Viewing Old Versions:
```powershell
git checkout v1.0              # Go to tagged version
git checkout abc1234           # Go to specific commit
git checkout main              # Back to main branch
git checkout dev               # Back to dev branch
```

### Saving Work Without Committing:
```powershell
# Need to switch branches but have uncommitted changes?
git stash                      # Save changes temporarily
git checkout other-branch      # Switch branch
git checkout original-branch   # Come back
git stash pop                  # Restore saved changes
```

---

## Current Setup

**Branches Created:**
- ✅ `main` - Stable, client-ready code
- ✅ `dev` - Active development (YOU ARE HERE)

**Next Steps:**
1. Continue daily work on `dev` branch
2. Commit regularly with descriptive messages
3. Push to GitHub frequently (backup!)
4. When ready for client demo, merge to `main` and tag

---

## Workflow Example Scenario

### Week 1: Development
```powershell
git checkout dev
# ... work on RBAC system ...
git commit -m "Added roles table"
# ... more work ...
git commit -m "Implemented permission checks"
git push origin dev
```

### Week 2: Client Demo Prep
```powershell
git checkout dev
git status  # Make sure everything is committed

git checkout main
git merge dev
git tag v1.1
git push origin main --tags

# Build executable
# Show to client
```

### Week 2: After Demo
```powershell
# Client wants changes - back to dev
git checkout dev
# ... implement feedback ...
git commit -m "Updated UI based on client feedback"
git push origin dev
```

### Week 3: Another Demo
```powershell
git checkout main
git merge dev
git tag v1.2
git push origin main --tags

# Build and demo again
```

---

## Best Practices

### ✅ DO:
- Work on `dev` branch daily
- Commit frequently with clear messages
- Push to GitHub often (backup!)
- Merge to `main` only when ready for client
- Tag every version shown to client
- Keep `main` always working/deployable
- Pull before starting work (especially on multiple computers)

### ❌ DON'T:
- Commit directly to `main` during development
- Show client the `dev` branch
- Delete branches with unmerged work
- Force push (`git push -f`) unless you know what you're doing
- Forget to push after committing (no backup!)

---

## Troubleshooting

### "I'm on the wrong branch!"
```powershell
git checkout dev  # Switch to dev
```

### "I committed to main by mistake!"
```powershell
git checkout dev
git cherry-pick abc1234  # Copy that commit to dev
git checkout main
git reset --hard HEAD~1  # Remove commit from main (CAREFUL!)
```

### "I have uncommitted changes and need to switch branches"
```powershell
git stash           # Save changes
git checkout dev    # Switch branch
git stash pop       # Restore changes
```

### "I don't know which version I showed the client"
```powershell
git tag  # List all tags
# Next time, always tag client demos!
```

### "My branches are out of sync"
```powershell
git checkout dev
git pull origin dev     # Get remote changes

# If conflicts occur:
# 1. Git will mark conflicting files
# 2. Edit files to resolve conflicts
# 3. git add resolved-files
# 4. git commit
```

---

## Visual Guide

### Your Current Situation (After Setup):

```
GitHub (Remote)
  ├── main branch (stable)
  └── dev branch (your work)

Your Computer
  ├── main branch (stable)
  └── dev branch (active) ← YOU ARE HERE
```

### After Making Changes:

```
1. Edit files
2. git add .
3. git commit -m "message"
4. git push origin dev
   
   ↓
   
Your changes now on GitHub (backed up!)
```

### When Preparing Client Demo:

```
dev branch (all your work)
   ↓
   git merge
   ↓
main branch (clean version)
   ↓
   git tag v1.1
   ↓
Build executable → Show to client
   ↓
git checkout dev (back to work)
```

---

## Quick Reference Card

| Task | Command |
|------|---------|
| See current branch | `git branch` |
| Switch to dev | `git checkout dev` |
| Switch to main | `git checkout main` |
| Commit changes | `git add . && git commit -m "message"` |
| Push to GitHub | `git push origin branch-name` |
| Get latest changes | `git pull origin branch-name` |
| Merge dev into main | `git checkout main && git merge dev` |
| Tag a version | `git tag v1.0` |
| Push tags | `git push origin --tags` |
| See old version | `git checkout v1.0` |
| Back to current work | `git checkout dev` |

---

## Remember

🎯 **Golden Rule**: `main` = always ready to show client, `dev` = your workshop

📝 **Tag every client demo**: Makes it easy to go back to what they saw

💾 **Push frequently**: Your work is backed up on GitHub

🔄 **Pull before working**: Especially important with multiple computers

---

## Next Learning Steps

1. Get comfortable with `git checkout` to switch branches
2. Practice committing and pushing to `dev` branch
3. When ready for first client demo, practice merging to `main`
4. Learn about `.gitignore` to exclude database files, etc.
5. Explore GitHub's web interface to visualize branches

---

**Remember**: Git is your safety net. You can always go back to any previous state. Don't be afraid to experiment!
