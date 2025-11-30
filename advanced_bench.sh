#!/bin/bash
set -e

if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root (or with sudo) because it modifies system settings." >&2
  exit 1
fi

DEFAULT_NB=100000
NB=${1:-$DEFAULT_NB}
CONDA_ENV_NAME="faiss-bench"

# Check for conda and initialize it if necessary
if ! command -v conda &>/dev/null; then
  echo "Conda not found in PATH. Attempting to initialize it..."
  # HARDCODED
  CONDA_SCRIPT="/users/dgrassi/miniforge3/etc/profile.d/conda.sh"
  if [ -f "$CONDA_SCRIPT" ]; then
    source "$CONDA_SCRIPT"
  else
    echo "Error: Could not find conda initialization script at $CONDA_SCRIPT."
    echo "Please ensure Miniforge3 is installed at /users/dgrassi/miniforge3 or update the script with the correct path."
    exit 1
  fi
  # Re-check for conda after attempting to initialize it.
  if ! command -v conda &>/dev/null; then
    echo "Error: Failed to initialize conda. Please check your installation."
    exit 1
  fi
  echo "Conda initialized successfully."
fi

# Check for THP
THP_PATH="/sys/kernel/mm/transparent_hugepage/enabled"
if [ ! -f "$THP_PATH" ]; then
  echo "Error: Transparent Hugepage setting not found at $THP_PATH."
  exit 1
fi

# Check for the conda environment, create if doesn't exist.
if ! conda env list | grep -q "$CONDA_ENV_NAME"; then
  echo "Creating conda environment '$CONDA_ENV_NAME'..."
  conda create -n "$CONDA_ENV_NAME" -y
  echo "Conda environment created."
  echo ""
  echo "Installing faiss-cpu=1.12.0..."
  conda install -n "$CONDA_ENV_NAME" -c pytorch faiss-cpu=1.12.0 -y
  echo "Dependencies installed."
else
  echo "Conda environment '$CONDA_ENV_NAME' already exists. Skipping creation and installation."
fi
echo ""

# Benchmarking Loop
RESULTS_DIR="test_results/faiss"
NB_VALUES=(100000 1000000)

echo "Starting benchmark runs. This will require sudo to change system settings."
echo "Creating results directory at $RESULTS_DIR..."
mkdir -p "$RESULTS_DIR"
echo "Will test with NB values: ${NB_VALUES[*]}"
echo ""

for nb in "${NB_VALUES[@]}"; do
  echo "====================================================="
  echo "=== Starting Benchmark for NB = $nb ==="
  echo "====================================================="

  for setting in always never madvise; do
    echo "-----------------------------------------------------"
    echo "--- Running benchmark with THP set to '$setting' ---"
    echo "-----------------------------------------------------"
    echo "Clearing system page cache..."
    sudo bash -c "sync && echo 3 > /proc/sys/vm/drop_caches"
    sleep 2
    echo "Setting transparent_hugepage/enabled to '$setting'..."
    sudo bash -c "echo $setting > $THP_PATH"
    echo "Current THP setting: $(cat $THP_PATH)"
    echo ""
    BENCH_OUTPUT="$RESULTS_DIR/hnsw_results_${setting}_nb${nb}.txt"
    PERF_OUTPUT="$RESULTS_DIR/perf_results_${setting}_nb${nb}.txt"
    echo "Running benchmark script for nb=$nb..."
    echo "Benchmark output will be saved to: $BENCH_OUTPUT"
    echo "Perf statistics will be saved to: $PERF_OUTPUT"
    echo ""

    # Activate conda environment and run the benchmark under 'perf stat'
    conda run -n "$CONDA_ENV_NAME" perf stat \
      -e "cache-references,cache-misses,dTLB-loads,dTLB-load-misses,iTLB-loads,iTLB-load-misses,LLC-loads,LLC-load-misses" \
      -o "$PERF_OUTPUT" \
      -- \
      python faiss/perf_tests/bench_hnsw.py --nb "$nb" >"$BENCH_OUTPUT"

    echo ""
    echo "--- Finished run for '$setting' with nb=$nb ---"
    echo ""
  done
done

# Reset THP to madvise
echo "Resetting Transparent Hugepage setting to 'madvise'."
sudo bash -c "echo madvise > $THP_PATH"

echo "-----------------------------------------------------"
echo "All benchmarks complete."
echo "Final THP setting: $(cat $THP_PATH)"
echo "-----------------------------------------------------"
