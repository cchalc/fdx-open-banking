# fdx-open-banking recipes. See CLAUDE.md for the workflow.
# bash (not fish) so recipes behave the same on Linux CI.

set shell := ["bash", "-euo", "pipefail", "-c"]

# Databricks profile for the bundle's dev target (see databricks.yml)
profile := "fevm-cjc"

# Show recipes
default:
    @just --list

# === ENV ===

# Create/refresh the shared venv (~/.virtualenvs/fdx-open-banking)
setup:
    uv sync

# === QUALITY ===

# Lint + format check
lint:
    uv run ruff check .
    uv run ruff format --check .

# Auto-fix lint + format
fmt:
    uv run ruff check --fix .
    uv run ruff format .

# Run the test suite
test *args:
    uv run pytest {{args}}

# lint + test (same gate as CI)
check: lint test

# === LOCAL FDX MOCKS (podman) ===

# Start the Mastercard FDX mock auth + resource servers
mocks-up:
    podman compose -f mock/compose.yaml up -d

# Stop the mock servers
mocks-down:
    podman compose -f mock/compose.yaml down

# Seed synthetic Canadian accounts/transactions into the resource mock
seed *args:
    uv run python -m fdx_open_banking.seed {{args}}

# Pull FDX data from the mocks and land raw JSON (local dir or UC Volume)
ingest *args:
    uv run python -m fdx_open_banking.land {{args}}

# === DATABRICKS BUNDLE ===

# Validate the bundle against the dev target
bundle-validate target="dev":
    databricks bundle validate -t {{target}} --profile {{profile}}

# Deploy the bundle (ask before running against a shared workspace)
bundle-deploy target="dev":
    databricks bundle deploy -t {{target}} --profile {{profile}}
