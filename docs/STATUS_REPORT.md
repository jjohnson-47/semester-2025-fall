# Project Status Report

Generated: 2025-09-04T18:30:44-08:00


**Environment**

- **Python**: 3.13.6
- **uv**: uv 0.8.14

**Checks**

- **JSON validate**: OK
- **Format check**: OK
- **Lint**: OK
- **Suppress guard**: OK
- **Typecheck (mypy)**: OK
- **Tests (pytest)**: OK
- **Coverage XML**: OK
- **Coverage ratchet**: OK

**Health Endpoints**

- **Defined**: yes

**Summaries**

- Validate:   Loaded schema: course_guide
- Format: 87 files already formatted
- Lint: All checks passed!
- Suppress: 
- Mypy: Success: no issues found in 13 source files
- Pytest: Coverage XML written to file build/coverage.xml [32mRequired test coverage of 50% reached. Total coverage: 50.73% [0m[32m======================= [32m[1m195 passed[0m, [33m2 skipped[0m[32m in 11.39s[0m[32m ========================[0m 
- Ratchet: uv run python scripts/ci/coverage_ratchet.py coverage.xml Current coverage: 52.67% Baseline coverage: 52.74% (allowed drop ≤ 0.5pp) 

**Remaining Failing Checks**

- None — all checks passed.

**Artifacts**

- **Report**: docs/STATUS_REPORT.md
- **Coverage XML**: build/coverage.xml (if generated)
