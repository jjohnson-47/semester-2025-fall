# Testing

## Markers
- `@pytest.mark.unit` – fast unit tests
- `@pytest.mark.integration` – DB and service integration
- `@pytest.mark.smoke` – basic end-to-end sanity

## Commands
- `make test UNIT=1` – unit tests
- `make test INTEGRATION=1` – integration tests
- `make test SMOKE=1` – smoke tests
- `make cov-xml` – produce coverage.xml for CI upload

## DB Execution Timeout (Tests)

SQLite doesn’t have a true per-statement timeout, so for tests we enforce one using the SQLite progress handler:

- Env var: `TEST_DB_STATEMENT_TIMEOUT_MS` (milliseconds). If set, all DB connections apply a watchdog that aborts any SQL statement exceeding the limit.
- Implementation: see `dashboard/db/repo.py` (`set_progress_handler`). On timeout, SQLite raises `sqlite3.OperationalError`.

### Simulate locally

```bash
# Run full suite with a 2s statement timeout
TEST_DB_STATEMENT_TIMEOUT_MS=2000 uv run pytest -v

# Or with Makefile partitions
TEST_DB_STATEMENT_TIMEOUT_MS=2000 make test UNIT=1
```

If a query exceeds the limit, tests will fail with an OperationalError; add logging around the offending path to diagnose.
