from bm25s.tokenization import Tokenized
import jieba
import bm25s
from typing import List, Union
from tqdm.auto import tqdm


def tokenize(
    texts,
    return_ids: bool = True,
    show_progress: bool = True,
    leave: bool = False,
) -> Union[List[List[str]], Tokenized]:
    if isinstance(texts, str):
        texts = [texts]

    corpus_ids = []
    token_to_index = {}

    for text in tqdm(
        texts, desc="Split strings", leave=leave, disable=not show_progress
    ):

        splitted = jieba.lcut(text)
        doc_ids = []

        for token in splitted:
            if token not in token_to_index:
                token_to_index[token] = len(token_to_index)

            token_id = token_to_index[token]
            doc_ids.append(token_id)

        corpus_ids.append(doc_ids)

    # Create a list of unique tokens that we will use to create the vocabulary
    unique_tokens = list(token_to_index.keys())

    vocab_dict = token_to_index

    # Return the tokenized IDs and the vocab dictionary or the tokenized strings
    if return_ids:
        return Tokenized(ids=corpus_ids, vocab=vocab_dict)

    else:
        # We need a reverse dictionary to convert the token IDs back to tokens
        reverse_dict = unique_tokens
        # We convert the token IDs back to tokens in-place
        for i, token_ids in enumerate(
            tqdm(
                corpus_ids,
                desc="Reconstructing token strings",
                leave=leave,
                disable=not show_progress,
            )
        ):
            corpus_ids[i] = [reverse_dict[token_id] for token_id in token_ids]

        return corpus_ids


bm25s.tokenize = tokenize

corpus = [
    "今天天气晴朗，我的心情美美哒",
    "小明和小红一起上学",
    "我们来试一试吧",
    "我们一起学猫叫",
    "我和Faker五五开",
    "明天预计下雨，不能出去玩了",
]


# Tokenize the corpus and index it
corpus_tokens = bm25s.tokenize(corpus)
print(corpus_tokens)

retriever = bm25s.BM25(corpus=corpus)
retriever.index(corpus_tokens)

query = "明天天气怎么样"
query_tokens = bm25s.tokenize(query)
docs, scores = retriever.retrieve(query_tokens, k=3)
print(f"Best result (score: {scores[0, 0]:.2f}): {docs[0, 0]}")
print(docs, scores)