# V2 Architecture Migration Complete

## Migration Status: ✅ COMPLETE

The semester-2025-fall repository has been fully migrated to the V2 architecture as the default mode.

## Changes Implemented

### 1. Documentation Updates

#### CLAUDE.md (NEW)
- Created comprehensive AI agent instructions
- Emphasizes V2 as the only supported mode
- Includes project structure, deployment workflow, and troubleshooting
- Location: `/CLAUDE.md`

#### README.md (UPDATED)
- Title now includes "(V2 Architecture)"
- All commands show `BUILD_MODE=v2` explicitly
- Added deployment section with dashboard instructions
- Emphasized V2 features and benefits
- Marked legacy as deprecated

#### V2_DEPLOYMENT_GUIDE.md (NEW)
- Complete deployment documentation
- Three deployment methods documented
- Security configuration details
- Troubleshooting guide
- Location: `/docs/V2_DEPLOYMENT_GUIDE.md`

### 2. Code Updates

#### Makefile
- **BUILD_MODE now defaults to v2** (was: legacy)
- Added deprecation warnings for legacy mode
- Updated help text to show V2 architecture
- Shows current BUILD_MODE in help output

#### scripts/services/projection_adapter.py
- Changed default from "legacy" to "v2"
- Added Python deprecation warnings
- Updated docstrings to reflect v2 as default

#### scripts/build_pipeline.py
- Updated BUILD_MODE checks to default to v2
- Added deprecation warnings for legacy mode

#### dashboard/app.py
- Fixed syllabus/schedule serving routes
- Improved response headers for HTML content
- Updated for v2 naming conventions

#### dashboard/templates/dashboard.html
- **Removed legacy document toggle feature**
- Cleaned up navigation for v2 alignment
- Removed iframe preview (replaced with proper routes)
- Focused dashboard on task management

### 3. Style System Integration

#### scripts/utils/style_system.py
- Added course-specific color themes:
  - MATH221: Blue (#0066cc)
  - MATH251: Green (#006600)
  - STAT253: Orange (#cc6600)
- Generates embedded CSS for standalone viewing

#### assets/css/courses/
- Updated course CSS files with proper colors
- Aligned with v2 color scheme

### 4. Dashboard UX Improvements

#### Navigation Structure
**Course Content** dropdown:
- Preview All Materials → `/preview`
- View Syllabi → `/syllabi`
- View Schedules → `/schedules`
- Download All (DOCX) → `/api/export/docx`

**Deploy** dropdown:
- Preview Embed
- Embed Generator
- Production Site

**System** dropdown:
- Build Statistics
- Task API
- Local Server

#### New Templates
- `syllabi_listing.html` - Professional card layout
- `schedules_listing.html` - Schedule overview cards

## Breaking Changes

### For Users
1. `BUILD_MODE=legacy` now shows deprecation warnings
2. Default build mode changed from legacy to v2
3. Dashboard document toggle removed

### For Developers
1. `is_v2_enabled()` now returns True by default
2. Legacy mode requires explicit `BUILD_MODE=legacy`
3. All new code must support v2 mode only

## Migration Path for Existing Users

### If you have existing builds:
```bash
# Clean old builds
make clean

# Rebuild with v2 (now default)
make all

# Verify output
ls -la build/syllabi/
```

### If you have custom scripts:
1. Remove any `BUILD_MODE=legacy` settings
2. Test with default v2 mode
3. Update any hardcoded paths

### If you use CI/CD:
1. Remove `BUILD_MODE=legacy` from pipelines
2. V2 is now the default
3. Test deployment workflow

## Testing Performed

✅ Makefile defaults to v2
✅ Deprecation warnings appear for legacy mode
✅ Dashboard works with v2 architecture
✅ Syllabi/schedules generate with embedded CSS
✅ Course colors properly applied
✅ Deployment documentation complete
✅ All navigation links functional

## Next Steps

### Phase 1 (Current) - COMPLETE
- [x] V2 as default mode
- [x] Legacy shows deprecation warnings
- [x] Documentation updated
- [x] Dashboard aligned with v2

### Phase 2 (Next Release)
- [ ] Remove legacy code paths
- [ ] Remove BUILD_MODE checks (v2 only)
- [ ] Clean up unused legacy files
- [ ] Update tests for v2 only

### Phase 3 (Future)
- [ ] Enhanced v2 features
- [ ] Additional projections
- [ ] Performance optimizations
- [ ] Extended rule engine

## Commands Quick Reference

```bash
# Everything now defaults to v2
make all          # Builds with v2
make dash         # Dashboard with v2
make syllabi      # V2 syllabi generation
make schedules    # V2 schedules

# Legacy mode (deprecated)
BUILD_MODE=legacy make all  # Shows warning

# Check current mode
echo $BUILD_MODE  # Should be empty or "v2"
make help         # Shows "Current mode: BUILD_MODE=v2"
```

## Support

For questions about the v2 architecture:
1. See `/CLAUDE.md` for AI agent instructions
2. See `/docs/V2_DEPLOYMENT_GUIDE.md` for deployment
3. See `/README.md` for general documentation
4. Check deprecation warnings for migration hints

---

**The V2 architecture is now the standard. Legacy mode will be removed in the next release.**

*Migration completed: August 26, 2025*