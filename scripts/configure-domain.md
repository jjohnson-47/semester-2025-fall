# Cloudflare Pages Domain Configuration

## Current Status
- **Primary Domain**: https://courses.jeffsthings.com/ ✅ Working
- **Fallback URL**: https://production.jeffsthings-courses.pages.dev/

## Steps to Configure Custom Domain

### 1. In Cloudflare Dashboard

1. Go to your Cloudflare Pages project: `jeffsthings-courses`
2. Navigate to "Custom domains" tab
3. Click "Set up a custom domain"
4. Enter: `courses.jeffsthings.com`
5. Cloudflare will automatically configure the DNS records

### 2. Alternative: Manual DNS Configuration

If you prefer to set up DNS manually or if auto-configuration fails:

Add these DNS records to your jeffsthings.com zone:

```
Type: CNAME
Name: courses
Content: jeffsthings-courses.pages.dev
Proxy status: Proxied (orange cloud)
TTL: Auto
```

### 3. Verify Configuration

After DNS propagation (usually within minutes):
- Visit: https://courses.jeffsthings.com/
- Check manifest: https://courses.jeffsthings.com/manifest.json
- Test embed page: https://courses.jeffsthings.com/courses/MATH221/fall-2025/syllabus/embed/

## Updated URLs for Iframe Embedding

Once the domain is configured, use these URLs in your iframes:

### For Blackboard Ultra
```html
<!-- MATH221 Syllabus -->
<iframe src="https://courses.jeffsthings.com/courses/MATH221/fall-2025/syllabus/embed/" 
        width="100%" 
        height="800" 
        frameborder="0">
</iframe>

<!-- MATH251 Schedule -->
<iframe src="https://courses.jeffsthings.com/courses/MATH251/fall-2025/schedule/embed/" 
        width="100%" 
        height="600" 
        frameborder="0">
</iframe>
```

### Iframe Generator Tool
Visit: https://courses.jeffsthings.com/embed/generator/

This tool will help generate the correct iframe code with proper dimensions for each course document.

## Security Headers Status

✅ **Fixed**: The CSP headers have been updated to allow:
- Embedding from *.jeffsthings.com domains
- Embedding from *.pages.dev domains  
- Embedding in Blackboard (*.blackboard.com)
- Local testing (localhost)
- X-Frame-Options set to ALLOWALL

## Domain Configuration Complete

The custom domain has been successfully configured and is now the primary URL for all course content. The Pages URL remains available as a fallback.