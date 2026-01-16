# 🧹 Privacy & Cleanup Checklist for Public Repo

## 🔴 CRITICAL - Must Delete/Change Before Push

### 1. Database Files (Contains Your Personal Data)
**ACTION: DELETE THESE FILES**
```bash
rm /opt/CasettaFit/app/casettafit.db
rm /opt/CasettaFit/app/casettafit_1-7_0930.db
```
- These contain your personal workout data, gym addresses, user info
- .gitignore already excludes `*.db` but delete existing ones

### 2. Uploaded Images (Personal Photos)
**ACTION: DELETE THESE FILES**
```bash
rm /opt/CasettaFit/app/static/uploads/gyms/*.png
rm /opt/CasettaFit/app/static/uploads/gyms/*.jpeg
rm /opt/CasettaFit/app/static/uploads/profiles/*.jpg
```
Keep only the `.gitkeep` files:
```bash
# Verify only .gitkeep remains:
ls -la /opt/CasettaFit/app/static/uploads/gyms/
ls -la /opt/CasettaFit/app/static/uploads/profiles/
```

### 3. Git History - Author Information
**FOUND IN GIT:**
- **Author Name**: Zak Chalupka
- **Author Email**: zak@casettacloud.com

**ACTION: REWRITE GIT HISTORY** (if you want to anonymize)
```bash
cd /opt/CasettaFit

# Option A: Start fresh (recommended)
rm -rf .git
git init
git add .
git commit -m "Initial commit"

# Option B: Keep history but change author (more complex)
# See: https://docs.github.com/en/github/using-git/changing-author-info
```

**OR** just update git config for future commits:
```bash
git config user.name "YourNewName"
git config user.email "your@email.com"
```

### 4. Personal Server Info in SSL_SETUP.md
**FILE**: `/opt/CasettaFit/SSL_SETUP.md`

**FOUND (Lines 96-102):**
- Server IP: 143.10.10.10
- Domain: fit.domain.com
- Old DNS IP: 143.244.210.65

**ACTION: Replace with generic examples**
Change to:
```markdown
## Example Configuration

**Server IP:** YOUR_SERVER_IP  
**Domain:** your-domain.com  
**DNS Status:** Configure your DNS to point to your server
```

### 5. Username Reference
**FILE**: Multiple locations
**FOUND**: `casettalocal` (username)

**Files to update:**
- `/opt/CasettaFit/README.md` (line 261)
- `/opt/CasettaFit/casettafit.service` (lines 7-8)

**ACTION: Change to generic username**
Replace with: `casettafit` or `YOUR_USERNAME`

---

## 🟡 MEDIUM PRIORITY - Consider Changing

### 6. Default Admin Credentials (Line 162 in README)
**Currently:**
- Username: admin
- Password: adminpass

**This is OK** - it's a default that gets changed after installation. But consider adding stronger warning.

### 7. Domain Examples Throughout
**FOUND**: `fit.domain.com` in SSL_SETUP.md (multiple locations)

**ACTION**: Replace with generic example like `example.com` or `your-domain.com`

---

## 🟢 LOW PRIORITY - Optional

### 8. Local IPs (These are OK)
- `127.0.0.1:5000` - localhost (standard, keep as-is)
- `0.0.0.0:5000` - bind to all interfaces (standard, keep as-is)

These are generic development IPs and don't reveal anything personal.

---

## ✅ ALREADY SAFE (No Action Needed)

### .gitignore properly configured ✅
- Ignores `*.db` files
- Ignores `uploads/*` (except .gitkeep)
- Ignores `logs/*`
- Ignores `venv/`
- Ignores `.env`

### No environment secrets found ✅
- No API keys found
- No database passwords in code (uses local SQLite)
- No email credentials

### Marketing files are clean ✅
- COPY_PASTE_TEXT.md - generic template
- GITHUB_MARKETING.md - generic guide
- CHECKLIST.md - generic todo list

---

## 📋 Quick Cleanup Script

Run this to clean everything in one go:

```bash
#!/bin/bash
cd /opt/CasettaFit

# Remove databases
rm -f app/*.db

# Remove uploaded images (keep .gitkeep)
find app/static/uploads -type f ! -name '.gitkeep' -delete

# Remove logs (if any)
rm -f logs/*.log

# Remove venv (will be recreated on install)
rm -rf venv/

# Reset git (OPTIONAL - only if you want clean history)
# rm -rf .git
# git init
# git add .
# git commit -m "Initial commit"

echo "✅ Cleanup complete!"
echo ""
echo "⚠️  Remember to manually update:"
echo "   - SSL_SETUP.md (remove personal IPs/domains)"
echo "   - README.md (change 'casettalocal' to generic name)"
echo "   - casettafit.service (change 'casettalocal' user)"
echo "   - Git config (git config user.name / user.email)"
```

---

## 🚀 Before You Push to GitHub

### Final Checklist:
- [ ] Deleted all `.db` database files
- [ ] Deleted all uploaded images (gyms/profiles)
- [ ] Updated SSL_SETUP.md (removed personal IPs/domains)
- [ ] Updated README.md (generic username)
- [ ] Updated casettafit.service (generic username)
- [ ] Decided on git history (keep or reset)
- [ ] Updated git config with desired author info
- [ ] Verified .gitignore is working:
  ```bash
  git status
  # Should NOT show .db files or uploads
  ```
- [ ] Test that nothing personal appears:
  ```bash
  git grep -i "143.10.10.10"
  git grep -i "fit.domain.com"
  git grep -i "casettalocal"
  git grep -i "zak"
  git grep -i "casettacloud"
  ```

### Then push:
```bash
git remote add origin https://github.com/YOUR_USERNAME/CasettaFit.git
git branch -M main
git push -u origin main
```

---

## 📝 Notes

- **thoughts/** folder: Currently only contains COPY_PASTE_TEXT.md which is safe (marketing template)
- **screenshots/v1/**: These are safe to include (they show the app UI)
- **migrations/**: SQL migration scripts are safe (no personal data)

**Good luck with your public repo! 🎉**
