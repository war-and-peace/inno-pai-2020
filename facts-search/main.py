import json
import nltk
from nltk import tokenize
from nltk.stem.snowball import SnowballStemmer
import sys
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

DATASET_PATH = 'dataset/dataset.jsonl'
INDEX_PATH = 'index.ext'


def load_dataset(path_to_dataset):
    res = []
    with open(path_to_dataset, "r") as f:
        data = f.readlines()
        for d in data:
            res.append(json.loads(d)['claim'])
    return res


def build_tdm(dataset):
    '''
        Could not build TDM for the given dataset. Number of facts: 145449, number of unique terms: 17989.
        The process crashed because of memory limitations (exit code 137)
    '''

    stemmer = SnowballStemmer('english')
    words_set = {}
    terms = []
    index = 0
    for ind, fact in enumerate(dataset):
        for sentence in nltk.sent_tokenize(fact.lower()):
            ts = [stemmer.stem(word) for word in tokenize.word_tokenize(sentence) if
                  word not in (',', '.', ':', '-', ';', '?', '!', '"', "``", "`", "''")]
            for tm in ts:
                if tm not in words_set:
                    words_set[tm] = index
                    index += 1
                    terms.append(tm)

    print(f'Dictionary is built. Total of {len(terms)} terms in the dictionary')
    tdm = [[0] * len(dataset) for _ in range(len(terms))]
    for ind, fact in enumerate(dataset):
        for sentence in nltk.sent_tokenize(fact.lower()):
            ts = [stemmer.stem(word) for word in tokenize.word_tokenize(sentence) if
                  word not in (',', '.', ':', '-', ';', '?', '!', '"', "``", "`", "''")]
            for tm in ts:
                tdm[words_set[tm]][ind] += 1
    return tdm, terms


class Transformer:
    def __init__(self):
        self.model = SentenceTransformer('bert-base-nli-mean-tokens')

    def embed_all(self, sentences: list):
        return self.model.encode(sentences, show_progress_bar=True, num_workers=4)

    def embed(self, sentence: str):
        return self.model.encode([sentence])[0]


def build_index(data, dimensions=768):
    index = faiss.index_factory(dimensions, "L2norm,IVF2048_HNSW32,Flat")
    index.train(data)
    index.add(data)
    faiss.write_index(index, INDEX_PATH)
    return index


if __name__ == '__main__':
    dataset = load_dataset(DATASET_PATH)
    # print(f'Dataset loaded! Total of {len(dataset)} facts.')
    # tdm, terms = build_tdm(dataset)
    # # print(f'Dictionary is built. Total of {len(words)} words in the dictionary')
    # print(terms[:10])
    # print(len(tdm))
    # print(f'Size of TDM: {sys.getsizeof(tdm)}')

    # Method 2. Using sentence BERT model

    model = Transformer()
    save = False
    try:
        print('Found embeddings.txt file. Reading...')
        f = open('embeddings.txt', 'rb')
        embeddings = np.load(f)
    except IOError as err:
        save = True
        print('Embedding...')
        embeddings = model.embed_all(dataset)

    if save:
        with open('embeddings.txt', "wb") as f:
            np.save(f, embeddings)

    index = None
    try:
        print('Trying to load index from disk')
        index = faiss.read_index(INDEX_PATH)
    except:
        print('Index loading failed. Building new index...')
        index = build_index(embeddings)
        print('Building is finished!')

    queries = ['Linus Torvalds', 'Harry Potter', 'CPU', 'Computer Science', 'Tom Cruise', 'Football']
    query_embeddings = model.embed_all(queries)
    res = index.search(query_embeddings, 10)

    print()
    for ind, query in enumerate(queries):
        print(f'Answers for the query: "{query}":')
        for i, index in enumerate(res[1][ind]):
            print(f'\t{dataset[index]} - id: {index}, cosine similarity: {res[0][ind][i]}')

    ind1 = res[1][0][0]
    first = embeddings[ind1] / np.linalg.norm(embeddings[ind1])
    second = query_embeddings[0] / np.linalg.norm(query_embeddings[0])
