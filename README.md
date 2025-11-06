# Install conda

```
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh
```

# Install faiss

```
conda install -c pytorch faiss-cpu=1.12.0
```
