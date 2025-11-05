# Git Commands to Push to GitHub

Run these commands in order from the `tech-support-ai` directory:

## Step 1: Initialize Git (if not already initialized)
```bash
cd tech-support-ai
git init
```

## Step 2: Add Remote Repository
```bash
git remote add origin https://github.com/KeerthiVasan2113/Supportron.git
```

## Step 3: Add All Files
```bash
git add .
```

## Step 4: Commit Changes
```bash
git commit -m "Initial commit: Supportron IT Tech Support AI Chatbot"
```

## Step 5: Push to GitHub
```bash
git branch -M main
git push -u origin main
```

---

## If Repository Already Exists on GitHub

If the repository already has content, you may need to pull first:

```bash
git pull origin main --allow-unrelated-histories
```

Then push:
```bash
git push -u origin main
```

---

## Troubleshooting

**If you get authentication errors:**
- Use GitHub Personal Access Token instead of password
- Or use SSH: `git remote set-url origin git@github.com:KeerthiVasan2113/Supportron.git`

**If remote already exists:**
```bash
git remote set-url origin https://github.com/KeerthiVasan2113/Supportron.git
```

