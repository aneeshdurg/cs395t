#!/usr/bin/env python3
import numpy as np
import time
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection
from tqdm import tqdm

########################################
# Helpers: read fvecs/ivecs
########################################


def read_fvecs(path):
    data = np.fromfile(path, dtype=np.int32)
    dim = data[0]
    data = data.reshape(-1, dim + 1)
    return data[:, 1:].astype("float32")


def read_ivecs(path):
    data = np.fromfile(path, dtype=np.int32)
    dim = data[0]
    data = data.reshape(-1, dim + 1)
    return data[:, 1:]


########################################
# Benchmark helpers
########################################


def run_search(collection, queries, k, nprobe):
    search_params = {
        "metric_type": "L2",
        "params": {"nprobe": nprobe},
    }
    t0 = time.time()
    results = collection.search(
        data=queries.tolist(),
        anns_field="vec",
        param=search_params,
        limit=k,
        consistency_level="Strong",
    )
    latency = (time.time() - t0) * 1000.0  # ms
    ids = [res.ids for res in results]
    return np.array(ids), latency


def compute_recall(retrieved, groundtruth, k):
    correct = 0
    nq = len(retrieved)
    for i in range(nq):
        correct += len(set(retrieved[i][:k]) & set(groundtruth[i][:k]))
    return correct / (nq * k)


########################################
# Main
########################################


def main():
    # Paths (modify if needed)
    base_path = "DiskANN/build/data/sift/sift_base.fvecs"
    query_path = "DiskANN/build/data/sift/sift_query.fvecs"
    gt_path = "DiskANN/build/data/sift/sift_groundtruth.ivecs"

    print("Loading SIFT dataset …")
    xb = read_fvecs(base_path)
    xq = read_fvecs(query_path)
    gt = read_ivecs(gt_path)

    dim = xb.shape[1]
    print(f"Loaded base: {xb.shape}, queries: {xq.shape}, gt: {gt.shape}")

    ########################################
    # Milvus Lite: embedded database
    ########################################
    print("Starting embedded Milvus Lite …")
    # This creates a local file "milvus.db" and runs everything in-process.
    connections.connect("default", uri="./milvus.db")

    collection_name = "sift_1m"

    print(f"Dropping old collection (if exists): {collection_name}")
    collection = Collection(name=collection_name).drop()
    # try:
    #     Collection(name=collection_name).drop()
    # except Exception:
    #     pass

    # print("Creating collection …")
    # fields = [
    #     FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
    #     FieldSchema(name="vec", dtype=DataType.FLOAT_VECTOR, dim=dim),
    # ]
    # schema = CollectionSchema(fields)
    # collection = Collection(name=collection_name, schema=schema)

    # print("Inserting vectors in batches …")

    # batch_size = 2000
    # num = len(xb)
    # ids = np.arange(num)

    # for start in tqdm(range(0, num, batch_size)):
    #     end = min(start + batch_size, num)

    #     batch_ids = ids[start:end]
    #     batch_vecs = xb[start:end].tolist()

    #     collection.insert([batch_ids, batch_vecs])

    # collection.flush()
    # print("Insertion complete.")

    # # ########################################
    # # # Build index
    # # ########################################
    # print("Creating IVF_FLAT index …")
    # index_params = {
    #     "index_type": "IVF_FLAT",
    #     "metric_type": "L2",
    #     "params": {"nlist": 4096},
    # }
    # collection.create_index(field_name="vec", index_params=index_params)
    collection.load()

    ########################################
    # Benchmark
    ########################################
    print("\nRunning latency / recall sweep …")

    nprobe_list = [1, 4, 8, 16, 32, 64, 128]
    k = 10

    for nprobe in nprobe_list:
        retrieved, latency = run_search(collection, xq, k, nprobe)
        recall = compute_recall(retrieved, gt, k)
        print(f"nprobe={nprobe:3d} | recall={recall:.4f} | latency={latency:.1f} ms")

    print("\nBenchmark complete!")


if __name__ == "__main__":
    main()
