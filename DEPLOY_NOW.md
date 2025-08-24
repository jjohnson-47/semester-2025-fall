# 🚀 Deploy Now - Quick Steps

## 1. Configure GitHub Secrets (Required)

Go to: <https://github.com/jjohnson-47/semester-2025-fall/settings/secrets/actions>

### Add these SECRETS

**CLOUDFLARE_API_TOKEN**

```bash
gopass show -o cloudflare/tokens/projects/semester-2025-fall/pages
```

**CLOUDFLARE_ACCOUNT_ID**

```bash
gopass show -o cloudflare/account/id
# Should be: 13eb584192d9cefb730fde0cfd271328
```

### Add this VARIABLE (not secret)

Go to: Variables tab

**CF_PROJECT** = `jeffsthings-courses`

## 2. Trigger Deployment

1. Go to: <https://github.com/jjohnson-47/semester-2025-fall/actions>
2. Click "Cloudflare Pages Deploy" workflow
3. Click "Run workflow" button
4. Select:
   - Branch: `main`
   - Environment: `preview`
5. Click green "Run workflow" button

## 3. Monitor

Watch the Actions tab for the workflow to complete.

## 4. Verify

Once deployed, check:

```bash
curl https://jeffsthings-courses.pages.dev/manifest.json
```

Should return the empty manifest with all three courses.

---

**Status**:

- ✅ Workflow pushed and active
- ⏳ Awaiting secrets configuration
- ⏳ Ready to deploy empty structure
