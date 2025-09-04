# Migration Guide: Course System Refactor v1.1.0

## Overview

This guide documents the migration from the legacy course system to the new projection-based architecture with centralized rules and services.

## Migration Timeline

### Phase 1: Foundation (Completed)
- ✅ Schema v1.1.0 with stable IDs
- ✅ DateRules engine implementation  
- ✅ NormalizedCourse models with provenance
- ✅ CourseRulesEngine for normalization
- ✅ Build pipeline implementation

### Phase 2: Services (Completed)
- ✅ CourseService with projections
- ✅ ValidationGateway for integrity checks
- ✅ ProjectionAdapter for backward compatibility
- ✅ Builder integration layer

### Phase 3: Testing (Completed)
- ✅ Golden tests for validation
- ✅ Contract tests for compatibility
- ✅ Cross-course consistency tests

### Phase 4: Integration (In Progress)
- ⏳ Template migration to projections
- ⏳ Dashboard intelligence view
- ⏳ Full cutover preparation

## Key Changes

### 1. Data Model

**Before:**
```json
{
  "course_code": "MATH221",
  "name": "Linear Algebra",
  "schedule": [...]
}
```

**After:**
```json
{
  "_meta": {
    "version": "1.1.0",
    "stable_id": "math221-fall-2025-abc123",
    "checksum": "sha256..."
  },
  "course_code": "MATH221",
  "name": "Linear Algebra",
  "schedule": [...]
}
```

### 2. Service Layer

**Before:**
```python
# Direct file loading
data = json.load(open("content/courses/MATH221/syllabus.json"))
```

**After:**
```python
# Service-based loading with normalization
from scripts.services.course_service_complete import CourseService

service = CourseService(content_dir=Path("content"))
course = service.load_course("MATH221")
projection = service.get_projection("MATH221", "syllabus")
```

### 3. Validation

**Before:**
```python
# Ad-hoc validation in builders
if not data.get("instructor"):
    print("Warning: No instructor")
```

**After:**
```python
# Centralized validation gateway
from scripts.services.validation_gateway import ValidationGateway

gateway = ValidationGateway(course_service)
report = gateway.validate_course("MATH221")
print(f"Valid: {report.overall_valid}, Confidence: {report.confidence_score}")
```

### 4. Date Handling

**Before:**
```python
# Manual date adjustments
if date.weekday() in [5, 6]:  # Weekend
    date = date - timedelta(days=...)
```

**After:**
```python
# Centralized date rules
from scripts.rules.dates_full import DateRules, AssignmentType

date_rules = DateRules()
adjusted = date_rules.apply_rules(date, AssignmentType.HOMEWORK)
```

## Migration Steps

### Step 1: Update Dependencies

```bash
# Install required packages
uv pip install dataclasses typing pathlib
```

### Step 2: Run Schema Migration

```bash
# Migrate existing JSON files to v1.1.0
python scripts/schema/migrator.py --dry-run
python scripts/schema/migrator.py --backup
```

### Step 3: Update Builders

```python
# In build_syllabi.py
from scripts.builders.projection_adapter import ProjectionAdapter, BuilderIntegration

adapter = ProjectionAdapter(content_dir=Path("content"))
integration = BuilderIntegration(adapter)

# Patch existing builder
integration.patch_syllabus_builder(builder)
```

### Step 4: Validate Migration

```bash
# Run validation suite
pytest tests/test_golden_validation.py
pytest tests/test_contract_compatibility.py
```

### Step 5: Update Templates (Optional)

Templates can continue using the same context structure due to the ProjectionAdapter maintaining backward compatibility.

## Backward Compatibility

The system maintains full backward compatibility through:

1. **ProjectionAdapter**: Transforms new projections to legacy format
2. **BuilderIntegration**: Patches existing builders transparently
3. **Legacy field injection**: Adds expected fields automatically

## Rollback Plan

If issues arise:

1. **Restore backups**:
   ```bash
   cp content/courses/*/backup/*.json content/courses/*/
   ```

2. **Revert code**:
   ```bash
   git checkout main
   ```

3. **Clear caches**:
   ```bash
   rm -rf build/.cache
   rm -rf content/.cache
   ```

## Performance Considerations

- **Caching**: Projections are cached in memory and on disk
- **Lazy loading**: Data loaded only when needed
- **Parallel processing**: Build pipeline processes courses concurrently

## Testing Checklist

- [ ] All courses load successfully
- [ ] Projections generate without errors
- [ ] Validation reports are accurate
- [ ] Templates render correctly
- [ ] Dashboard displays properly
- [ ] No weekend due dates
- [ ] Checksums are stable
- [ ] Cache behavior is correct

## Troubleshooting

### Issue: Course fails to load
```python
# Check course directory exists
Path("content/courses/COURSE_ID").exists()

# Validate JSON structure
python scripts/validate_json.py
```

### Issue: Projection generation fails
```python
# Force regeneration
service.get_projection(course_id, projection_type, force_regenerate=True)

# Check cache directory permissions
ls -la build/.cache
```

### Issue: Validation errors
```python
# Get detailed validation report
report = gateway.validate_course(course_id)
for result in report.errors:
    print(f"{result.field}: {result.message}")
```

## Support

For issues or questions:
- Check `docs/ARCHITECTURE_REPORT.md` for system overview
- Review `docs/ORCHESTRATION_PLAN.md` for implementation details
- Run `make validate` for system health check

## Next Steps

After successful migration:

1. Remove legacy code paths
2. Optimize projection generation
3. Enhance validation rules
4. Add more intelligent date handling
5. Implement change detection
6. Add incremental builds