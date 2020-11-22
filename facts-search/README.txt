Description of the solution:
    First, tried building TDM matrix and doing PCA as suggested. However, because of the memory requirements
    this method did not work. It simply didn't fit into the memory.
    Second, instead of dong the above, Bert sentence transformer is used to get embeddings of the sentences.
    Then faiss HNSW index is built on these embeddings.
    Every query is first embedded and queried using the index.

ATTENTION:
    Embedding the sentences takes about an hour.
    So, I have uploaded the embeddings file here (around 400 MBs):
        https://drive.google.com/drive/folders/1QffTa_VojWZ2TyS9x1YBaHONjR6GGeE9?usp=sharing
    Building index takes about 5 minutes.

Python version 3.8 is used.