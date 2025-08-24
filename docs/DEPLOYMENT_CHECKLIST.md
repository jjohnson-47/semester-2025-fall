# Deployment Checklist - Empty Structure

## Pre-Deployment Verification ✅

### 1. Local Build Validation

- [x] Run `make build-site ENV=preview`
- [x] Verify `site/` directory created
- [x] Check `manifest.json` exists with correct structure
- [x] Verify `_headers` file with CSP `frame-ancestors 'none'`
- [x] Confirm no course content in manifest (empty structure)

### 2. Architecture Compliance

- [x] UV patterns used throughout (`$(PYTHON)` wrapper)
- [x] Clean separation between `build/` and `site/`
- [x] Single source of truth maintained
- [x] No hardcoded values or workarounds

### 3. Security Headers

```
✅ Content-Security-Policy with frame-ancestors 'none'
✅ Referrer-Policy: no-referrer
✅ X-Content-Type-Options: nosniff
✅ Permissions-Policy restrictions
```

## GitHub Configuration Required

### Secrets (Settings → Secrets and variables → Actions → Secrets)

1. **CLOUDFLARE_API_TOKEN**

   ```bash
   # Get from gopass
   gopass show -o cloudflare/tokens/projects/semester-2025-fall/pages
   ```

   - Required scope: Account → Cloudflare Pages:Edit

2. **CLOUDFLARE_ACCOUNT_ID**

   ```bash
   # Get from gopass
   gopass show -o cloudflare/account/id
   ```

### Variables (Settings → Secrets and variables → Actions → Variables)

3. **CF_PROJECT**
   - Value: `jeffsthings-courses`
   - Type: Repository variable (not secret)

## Deployment Steps

### Phase 0: Empty Structure (Current)

1. **Configure GitHub Secrets/Variables**
   - Add all three items above to repository settings

2. **Create Cloudflare Pages Project**

   ```bash
   # Option A: Use cf-go
   make pages-create

   # Option B: Manual in dashboard
   # Create project named "jeffsthings-courses"
   ```

3. **Trigger Initial Deployment**
   - Go to GitHub Actions tab
   - Select "Cloudflare Pages Deploy" workflow
   - Click "Run workflow"
   - Select environment: `preview`
   - Click green "Run workflow" button

4. **Monitor Deployment**
   - Watch Actions tab for progress
   - Check for green checkmark
   - Note deployment URL in logs

## Post-Deployment Verification

### 1. Check Deployment URL

```bash
# Should return 200
curl -I https://jeffsthings-courses.pages.dev

# Check manifest
curl https://jeffsthings-courses.pages.dev/manifest.json
```

Expected manifest:

```json
{
  "generated": "2025-08-24T...",
  "term": "fall-2025",
  "courses": {
    "MATH221": { "last_updated": "...", "has_custom_dates": true },
    "MATH251": { "last_updated": "...", "has_custom_dates": true },
    "STAT253": { "last_updated": "...", "has_custom_dates": true }
  }
}
```

### 2. Verify Security Headers

```bash
curl -I https://jeffsthings-courses.pages.dev | grep -i frame-ancestors
```

Should see: `frame-ancestors 'none'`

### 3. Confirm No Content Exposed

```bash
# These should return 404
curl https://jeffsthings-courses.pages.dev/courses/
curl https://jeffsthings-courses.pages.dev/courses/MATH221/
```

### 4. Check with cf-go (if available)

```bash
# Export credentials
export CLOUDFLARE_API_TOKEN=$(gopass show -o cloudflare/tokens/projects/semester-2025-fall/pages)
export CLOUDFLARE_ACCOUNT_ID=$(gopass show -o cloudflare/account/id)

# Check project status
make pages-status

# List deployments
make pages-deployments PROJECT=jeffsthings-courses
```

## Success Criteria

✅ **Deployment completes without errors**
✅ **Manifest accessible at `/manifest.json`**
✅ **CSP headers prevent iframe embedding**
✅ **No course content exposed (404 on `/courses/`)**
✅ **GitHub Actions workflow runs successfully**

## Next Phases (After Validation)

### Phase 1: Enable Syllabus

```bash
# Update site_build.py to include syllabus
$(PYTHON) scripts/site_build.py --include-docs syllabus
```

### Phase 2: Enable Schedule

```bash
# Include both syllabus and schedule
$(PYTHON) scripts/site_build.py --include-docs syllabus schedule
```

## Troubleshooting

### Deployment Fails

1. Check GitHub Actions logs for specific error
2. Verify secrets are correctly set
3. Ensure CF_PROJECT variable is set (not secret)
4. Check Cloudflare dashboard for project status

### 404 on Root

- This is expected for empty structure
- Only `/manifest.json` and `/_headers` exist

### Token Issues

```bash
# Re-verify token
make pages-verify-token

# Check token metadata
gopass show cloudflare/tokens/projects/semester-2025-fall/pages/meta
```

## Current Status

- [x] Code complete and tested
- [x] Architecture verified
- [x] Security headers configured
- [x] Documentation complete
- [ ] GitHub secrets configured (user action required)
- [ ] Pages project created (user action required)
- [ ] First deployment triggered (user action required)
- [ ] Deployment verified (pending)

---

**Ready for deployment.** Configure GitHub secrets and trigger workflow.
