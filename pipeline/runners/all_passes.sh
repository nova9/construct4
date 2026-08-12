#!/usr/bin/env bash

set -euo pipefail

RUNNER_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

bash "$RUNNER_DIR/first_pass.sh"
bash "$RUNNER_DIR/second_pass.sh"
bash "$RUNNER_DIR/third_pass.sh"
