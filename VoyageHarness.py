"""
Evaluate a Voyage embedding model using duplicate Quora questions.

Install:
    pip install datasets voyageai numpy

Run:
    python quora_retrieval.py
"""

from __future__ import annotations

import numpy as np
import voyageai
from datasets import load_dataset


# ==== Configuration ====

VOYAGE_API_KEY = ""  # Put your Voyage AI key here
MODEL_NAME = "voyage-4-large"
MAX_PAIRS = 100
BATCH_SIZE = 128
RANDOM_SEED = 42


def sample_positive_pairs(
    max_pairs: int,
    seed: int,
) -> list[tuple[str, str]]:
    """Load a reproducible sample of duplicate Quora questions."""

    print("📦 Loading Quora Question Pairs...")

    dataset = load_dataset("quora", split="train").shuffle(seed=seed)
    pairs: list[tuple[str, str]] = []

    for item in dataset:
        questions = item["questions"]["text"]

        if (
            item["is_duplicate"]
            and len(questions) == 2
            and all(isinstance(text, str) and text.strip() for text in questions)
        ):
            pairs.append((questions[0], questions[1]))

        if len(pairs) == max_pairs:
            break

    if not pairs:
        raise ValueError("No valid duplicate question pairs were found.")

    return pairs


def normalize(vectors: np.ndarray) -> np.ndarray:
    """L2-normalize a matrix of embedding vectors."""

    norms = np.linalg.norm(vectors, axis=1, keepdims=True)

    if np.any(norms == 0):
        raise ValueError("Voyage returned one or more zero-length embeddings.")

    return vectors / norms


def embed_texts(
    client: voyageai.Client,
    texts: list[str],
    input_type: str,
) -> np.ndarray:
    """Embed texts in batches and return normalized vectors."""

    batches: list[np.ndarray] = []

    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]

        response = client.embed(
            texts=batch,
            model=MODEL_NAME,
            input_type=input_type,
        )

        vectors = np.asarray(response.embeddings, dtype=np.float32)

        if not np.isfinite(vectors).all():
            raise ValueError("Voyage returned invalid embedding values.")

        batches.append(vectors)

    return normalize(np.vstack(batches))


def calculate_metrics(
    query_vectors: np.ndarray,
    document_vectors: np.ndarray,
) -> tuple[float, float, float]:
    """Calculate Top-1 accuracy, Recall@5, and MRR."""

    similarities = query_vectors @ document_vectors.T
    rankings = np.argsort(-similarities, axis=1)

    expected_documents = np.arange(len(query_vectors))
    correct_ranks = (
        np.argmax(rankings == expected_documents[:, np.newaxis], axis=1) + 1
    )

    top_1_accuracy = np.mean(correct_ranks == 1)
    recall_at_5 = np.mean(correct_ranks <= 5)
    mean_reciprocal_rank = np.mean(1.0 / correct_ranks)

    return top_1_accuracy, recall_at_5, mean_reciprocal_rank


def main() -> None:
    if not VOYAGE_API_KEY.strip():
        raise ValueError("Add your Voyage AI API key to VOYAGE_API_KEY.")

    pairs = sample_positive_pairs(MAX_PAIRS, RANDOM_SEED)
    query_texts, document_texts = map(list, zip(*pairs))

    print(f"🔍 Preparing {len(pairs)} duplicate question pairs...")
    print(f"🧠 Embedding with {MODEL_NAME}...")

    client = voyageai.Client(api_key=VOYAGE_API_KEY)

    query_vectors = embed_texts(client, query_texts, input_type="query")
    document_vectors = embed_texts(
        client,
        document_texts,
        input_type="document",
    )

    top_1, recall_5, mrr = calculate_metrics(
        query_vectors,
        document_vectors,
    )

    print(f"\n📊 Quora retrieval results — {MODEL_NAME}")
    print(f"   Top-1 Accuracy: {top_1:.2%}")
    print(f"   Recall@5:      {recall_5:.2%}")
    print(f"   MRR:           {mrr:.4f}")


if __name__ == "__main__":
    main()
