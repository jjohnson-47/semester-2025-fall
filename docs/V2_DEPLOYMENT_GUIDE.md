# V2 Architecture Deployment Guide

## Overview

This guide documents the complete deployment process for the V2 architecture, which features projection-based rendering, embedded CSS, and systematic rule enforcement.

## Architecture Summary

### Two-Repository System

1. **Content Factory** (this repository)
   - Path: `/home/verlyn13/Projects/jjohnson-47/semester-2025-fall`
   - Generates all course materials from JSON data
   - Dashboard: http://localhost:5055
   - Output: `build/` and `site/` directories

2. **Content Delivery** (Cloudflare Pages)
   - Primary URL: https://courses.jeffsthings.com/
   - Fallback URL: https://production.jeffsthings-courses.pages.dev/
   - Auto-deploys on push to main branch
   - Serves content with iframe support for Blackboard

## Deployment Methods

### Method 1: Dashboard One-Click Deploy (Recommended)

The dashboard provides a fully integrated deployment pipeline:

1. **Start Dashboard with V2 Mode**
   ```bash
   BUILD_MODE=v2 make dash
   ```

2. **Navigate to Dashboard**
   - Open http://localhost:5055
   - Login if required

3. **Deploy via UI**
   - Click **Deploy** button in navigation
   - Select **Deploy to Production**
   - Monitor progress in real-time

4. **Automatic Pipeline**
   The dashboard executes:
   - `BUILD_MODE=v2 make build-site` - Generate static site
   - Sync to deployment repository
   - Deploy to Cloudflare Workers
   - Verify iframe headers and URLs
   - Report success/failure

### Method 2: Command Line Deployment

For automated or scripted deployments:

```bash
# 1. Build with V2 architecture
BUILD_MODE=v2 make build-site

# 2. Verify build
ls -la site/

# 3. Commit changes
git add -A
git commit -m "Deploy: Update course materials"

# 4. Push to trigger deployment
git push origin main
```

### Method 3: GitHub Actions (CI/CD)

Automatic deployment on push to main:

```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Build V2 Site
        run: BUILD_MODE=v2 make build-site
      
      - name: Deploy to Cloudflare
        run: pnpm deploy
```

## V2 Build Process

### Key Components

1. **Projection System** (`scripts/services/projection_adapter.py`)
   - Transforms JSON data into view-specific projections
   - Enforces business rules (no weekend due dates)
   - Provides consistent data structure

2. **Style System** (`scripts/utils/style_system.py`)
   - Embeds CSS directly in HTML for standalone viewing
   - Course-specific themes:
     - MATH221: Blue (#0066cc)
     - MATH251: Green (#006600)
     - STAT253: Orange (#cc6600)

3. **Template System** (`templates/`)
   - Jinja2 templates with V2 support
   - `includes/styles.html.j2` - Centralized style management
   - Context-aware rendering (embedded vs linked CSS)

### Build Commands

```bash
# Full build with V2
BUILD_MODE=v2 make all

# Individual components
BUILD_MODE=v2 make syllabi    # Generate syllabi
BUILD_MODE=v2 make schedules   # Generate schedules
BUILD_MODE=v2 make pipeline    # Run full pipeline
BUILD_MODE=v2 make test        # Test rule enforcement

# Site generation
BUILD_MODE=v2 make build-site  # Generate site/ directory
```

## Verification Process

### Pre-Deployment Checks

1. **Validate JSON Data**
   ```bash
   make validate
   ```

2. **Test Rule Enforcement**
   ```bash
   BUILD_MODE=v2 make test
   ```

3. **Preview Locally**
   ```bash
   python -m http.server 8001 -d build/
   ```

### Post-Deployment Verification

1. **Check Production Site**
   - Visit https://courses.jeffsthings.com/
   - Verify all courses load
   - Test navigation links

2. **Verify Iframe Embedding**
   ```bash
   # Test CSP headers
   curl -I https://courses.jeffsthings.com/embed/syllabus/MATH221
   ```

3. **Test Blackboard Integration**
   - Embed test URL in Blackboard
   - Verify content displays correctly
   - Check for console errors

## Security Configuration

### CSP Headers (Cloudflare Worker)

```javascript
// Allows embedding in Blackboard
'Content-Security-Policy': 
  "frame-ancestors 'self' https://*.blackboard.com https://ku.blackboard.com;"
```

### CORS Settings

```javascript
'Access-Control-Allow-Origin': '*',
'Access-Control-Allow-Methods': 'GET, OPTIONS',
'X-Frame-Options': 'SAMEORIGIN'
```

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Ensure `BUILD_MODE=v2` is set
   - Run `make clean` before rebuild
   - Check `scripts/logs/` for errors

2. **Deployment Failures**
   - Verify GitHub Actions secrets
   - Check Cloudflare API tokens
   - Review deployment logs

3. **Iframe Not Loading**
   - Check CSP headers
   - Verify embed URLs
   - Test in different browsers

### Debug Commands

```bash
# Check V2 mode
echo $BUILD_MODE

# Verify projections
BUILD_MODE=v2 python -c "
from scripts.services.course_service import CourseService
s = CourseService(content_dir=Path('content'))
print('CourseService V2 ready')
"

# Test style system
python -c "
from scripts.utils.style_system import StyleSystem
s = StyleSystem()
print('StyleSystem ready')
"
```

## Migration from Legacy

### Deprecation Timeline

- **Phase 1** (Current): V2 available via BUILD_MODE flag
- **Phase 2** (Next Release): V2 becomes default
- **Phase 3** (Future): Legacy code removed

### Migration Checklist

- [ ] Update all build commands to use `BUILD_MODE=v2`
- [ ] Verify dashboard uses V2 mode
- [ ] Update CI/CD pipelines
- [ ] Test all deployment methods
- [ ] Document any custom workflows

## Best Practices

1. **Always use V2 mode** for production builds
2. **Test locally** before deploying
3. **Validate JSON** before building
4. **Monitor deployment** logs
5. **Verify production** after deploy
6. **Keep documentation** updated

## Support

- Check `dashboard/logs/` for dashboard issues
- Check `scripts/logs/` for build issues
- Review GitHub Actions logs for deployment issues
- See CLAUDE.md for AI agent instructions
- See README.md for general documentation

---

**Remember: V2 is the future. Legacy mode is deprecated and will be removed.**