sudo bash -c "echo never > /sys/kernel/mm/transparent_hugepage/enabled"

{
  python faiss/perf_tests/bench_hnsw.py --nb 100000
  python faiss/perf_tests/bench_hnsw.py --nb 100000
  python faiss/perf_tests/bench_hnsw.py --nb 100000
} | tee never_results.txt

sudo bash -c "echo always > /sys/kernel/mm/transparent_hugepage/enabled"

{
  python faiss/perf_tests/bench_hnsw.py --nb 100000
  python faiss/perf_tests/bench_hnsw.py --nb 100000
  python faiss/perf_tests/bench_hnsw.py --nb 100000
} | tee always_results.txt


