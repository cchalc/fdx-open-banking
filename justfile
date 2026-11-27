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

# Upstream mock sources, pinned (Apache-2.0). Bump deliberately.
mock_auth_sha := "d07daa721c252885610fd193e8ce09706ba28336"
mock_res_sha := "f2d5b602242114b8d9563bd77e491cccb1c6bc11"

# Clone the pinned mock server sources into vendor/ (gitignored)
mocks-fetch:
    #!/usr/bin/env bash
    set -euo pipefail
    for pair in "Fdx-Mock-Auth-Server:{{mock_auth_sha}}" "Fdx-Mock-Resource-Server:{{mock_res_sha}}"; do
      repo="${pair%%:*}"; sha="${pair##*:}"; dir="vendor/$repo"
      [ -d "$dir/.git" ] || git clone --quiet "https://github.com/Mastercard/$repo.git" "$dir"
      git -C "$dir" fetch --quiet origin "$sha"
      git -C "$dir" -c advice.detachedHead=false checkout --quiet "$sha"
      echo "$repo @ $sha"
    done

# Build (if needed) and start the Mastercard FDX mock auth + resource servers
mocks-up:
    podman compose -f mock/compose.yaml up -d --build

# Stop the mock servers
mocks-down:
    podman compose -f mock/compose.yaml down

# Seed synthetic Canadian accounts/transactions into the resource mock
seed *args:
    uv run python -m fdx_open_banking.seed {{args}}

# Log in through the mock's consent screen (auth code + PKCE) and save .local/token.json
login *args:
    uv run python -m fdx_open_banking.login {{args}}

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
