#!/bin/bash
set -e

if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root (or with sudo) because it modifies system settings." >&2
  exit 1
fi

# Check for THP
THP_PATH="/sys/kernel/mm/transparent_hugepage/enabled"
if [ ! -f "$THP_PATH" ]; then
  echo "Error: Transparent Hugepage setting not found at $THP_PATH."
  exit 1
fi

# Benchmarking Loop
RESULTS_DIR="test_results/diskann"

echo "Starting benchmark runs. This will require sudo to change system settings."
echo "Creating results directory at $RESULTS_DIR..."
mkdir -p "$RESULTS_DIR"
echo ""

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
  BENCH_OUTPUT="$RESULTS_DIR/diskann_results_${setting}.txt"
  PERF_OUTPUT="$RESULTS_DIR/diskann_perf_results_${setting}.txt"
  echo "Running benchmark script for nb=$nb..."
  echo "Benchmark output will be saved to: $BENCH_OUTPUT"
  echo "Perf statistics will be saved to: $PERF_OUTPUT"
  echo ""

  # Activate conda environment and run the benchmark under 'perf stat'
  perf stat \
    -e "page-faults,cache-references,cache-misses,dTLB-loads,dTLB-load-misses,iTLB-loads,iTLB-load-misses,LLC-loads,LLC-load-misses" \
    -o "$PERF_OUTPUT" \
    -- \
    ./setup_diskann.sh bench >"$BENCH_OUTPUT"

  echo ""
  echo "--- Finished run for '$setting' ---"
  echo ""
done

# Reset THP to madvise
echo "Resetting Transparent Hugepage setting to 'madvise'."
sudo bash -c "echo madvise > $THP_PATH"

echo "-----------------------------------------------------"
echo "All benchmarks complete."
echo "Final THP setting: $(cat $THP_PATH)"
echo "-----------------------------------------------------"
