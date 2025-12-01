#!/bin/bash
install_deps() {
  sudo apt install make cmake g++ libaio-dev libgoogle-perftools-dev clang-format libboost-all-dev
  sudo apt install libmkl-full-dev
}

build() {
  pushd DiskANN/
  mkdir -p build && cd build && cmake -DCMAKE_BUILD_TYPE=Release .. && make -j
  popd
}

setup_bench() {
  mkdir -p DiskANN/build/data
  pushd DiskANN/build/data
  wget ftp://ftp.irisa.fr/local/texmex/corpus/sift.tar.gz
  tar -xf sift.tar.gz
  cd ..
  ./apps/utils/fvecs_to_bin float data/sift/sift_learn.fvecs data/sift/sift_learn.fbin
  ./apps/utils/fvecs_to_bin float data/sift/sift_query.fvecs data/sift/sift_query.fbin
  ./apps/utils/compute_groundtruth  --data_type float --dist_fn l2 --base_file data/sift/sift_learn.fbin --query_file  data/sift/sift_query.fbin --gt_file data/sift/sift_query_learn_gt100 --K 100
  ./apps/build_memory_index  --data_type float --dist_fn l2 --data_path data/sift/sift_learn.fbin --index_path_prefix data/sift/index_sift_learn_R32_L50_A1.2 -R 32 -L 50 --alpha 1.2
  popd
}

bench() {
  pushd DiskANN/build
  ./apps/search_memory_index  --data_type float --dist_fn l2 --index_path_prefix data/sift/index_sift_learn_R32_L50_A1.2 --query_file data/sift/sift_query.fbin  --gt_file data/sift/sift_query_learn_gt100 -K 10 -L 10 20 30 40 50 100 --result_path data/sift/res
  popd
}

$@
