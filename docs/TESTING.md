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

