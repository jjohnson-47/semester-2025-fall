# Blackboard iframe Embed Codes - Fall 2025

Generated: August 26, 2025

## Production URLs

All iframe codes below use the production Cloudflare Pages deployment at `https://courses.jeffsthings.com/`

## MATH 221 - Applied Calculus

### Syllabus (Embed Version - No Calendar)
```html
<iframe src="https://courses.jeffsthings.com/courses/MATH221/fall-2025/syllabus/embed/" 
        width="100%" 
        height="800" 
        frameborder="0"
        title="MATH221 Syllabus">
</iframe>
```

### Syllabus (Full Version - With Calendar)
```html
<iframe src="https://courses.jeffsthings.com/courses/MATH221/fall-2025/syllabus/" 
        width="100%" 
        height="800" 
        frameborder="0"
        title="MATH221 Syllabus with Calendar">
</iframe>
```

### Course Schedule
```html
<iframe src="https://courses.jeffsthings.com/courses/MATH221/fall-2025/schedule/embed/" 
        width="100%" 
        height="800" 
        frameborder="0"
        title="MATH221 Schedule">
</iframe>
```

---

## MATH 251 - Calculus I

### Syllabus (Embed Version - No Calendar)
```html
<iframe src="https://courses.jeffsthings.com/courses/MATH251/fall-2025/syllabus/embed/" 
        width="100%" 
        height="800" 
        frameborder="0"
        title="MATH251 Syllabus">
</iframe>
```

### Syllabus (Full Version - With Calendar)
```html
<iframe src="https://courses.jeffsthings.com/courses/MATH251/fall-2025/syllabus/" 
        width="100%" 
        height="800" 
        frameborder="0"
        title="MATH251 Syllabus with Calendar">
</iframe>
```

### Course Schedule
```html
<iframe src="https://courses.jeffsthings.com/courses/MATH251/fall-2025/schedule/embed/" 
        width="100%" 
        height="800" 
        frameborder="0"
        title="MATH251 Schedule">
</iframe>
```

---

## STAT 253 - Applied Statistics

### Syllabus (Embed Version - No Calendar)
```html
<iframe src="https://courses.jeffsthings.com/courses/STAT253/fall-2025/syllabus/embed/" 
        width="100%" 
        height="800" 
        frameborder="0"
        title="STAT253 Syllabus">
</iframe>
```

### Syllabus (Full Version - With Calendar)
```html
<iframe src="https://courses.jeffsthings.com/courses/STAT253/fall-2025/syllabus/" 
        width="100%" 
        height="800" 
        frameborder="0"
        title="STAT253 Syllabus with Calendar">
</iframe>
```

### Course Schedule
```html
<iframe src="https://courses.jeffsthings.com/courses/STAT253/fall-2025/schedule/embed/" 
        width="100%" 
        height="800" 
        frameborder="0"
        title="STAT253 Schedule">
</iframe>
```

---

## Blackboard Integration Instructions

### Adding to a Course Page

1. In Blackboard Ultra, navigate to your course
2. Click **"Create"** → **"Document"** 
3. Click the **"+"** button to add content
4. Select **"HTML"** from the content options
5. Copy and paste the iframe code above
6. Click **"Save"**

### Recommended Settings

- **Height**: 800px works well for most content
- **Width**: Always use 100% for responsive design
- **Frameborder**: Set to 0 for clean appearance
- **Title**: Include for accessibility

### Testing the Embed

1. After saving, preview the page
2. Check that content loads properly
3. Verify scrolling works if needed
4. Test on mobile device/responsive view

### Troubleshooting

If the iframe doesn't load:
1. Check that you're using HTTPS URLs
2. Verify the course code is correct (MATH221, not MATH 221)
3. Clear browser cache
4. Try in an incognito/private window

### Alternative: Direct Links

If iframes are not working, you can provide direct links:

**MATH 221**
- Syllabus: https://courses.jeffsthings.com/courses/MATH221/fall-2025/syllabus/
- Schedule: https://courses.jeffsthings.com/courses/MATH221/fall-2025/schedule/

**MATH 251**
- Syllabus: https://courses.jeffsthings.com/courses/MATH251/fall-2025/syllabus/
- Schedule: https://courses.jeffsthings.com/courses/MATH251/fall-2025/schedule/

**STAT 253**
- Syllabus: https://courses.jeffsthings.com/courses/STAT253/fall-2025/syllabus/
- Schedule: https://courses.jeffsthings.com/courses/STAT253/fall-2025/schedule/

---

## Features of V2 Architecture

All embedded content includes:
- ✅ **Embedded CSS** - No external dependencies
- ✅ **Course Colors** - MATH221 (Blue), MATH251 (Green), STAT253 (Orange)
- ✅ **Mobile Responsive** - Works on all devices
- ✅ **No Weekend Due Dates** - Systematically enforced
- ✅ **Blackboard Compatible** - Proper CSP headers configured

---

## Local Testing

To test locally before deploying to Blackboard:

```bash
# Start local server
python -m http.server 8001 -d site/

# Test URLs (replace localhost with your production URL for Blackboard)
http://localhost:8001/courses/MATH221/fall-2025/syllabus/embed/
http://localhost:8001/courses/MATH251/fall-2025/syllabus/embed/
http://localhost:8001/courses/STAT253/fall-2025/syllabus/embed/
```

---

## Support

For issues or updates:
1. Check that production site is live: https://courses.jeffsthings.com/
2. Verify CSP headers allow Blackboard domain
3. Contact support if iframe continues to fail

Last Updated: August 26, 2025
Generated with V2 Architecture