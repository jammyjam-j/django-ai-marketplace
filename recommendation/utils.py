import json
import os
import pickle
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np
from django.conf import settings
from langchain.embeddings.base import Embeddings
from langchain.vectorstores.faiss import FAISS
from pydantic import ValidationError


def load_json(file_path: str) -> Dict[str, Any]:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: str) -> None:
    path = Path(file_path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_pickle(file_path: str) -> Any:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Pickle file not found: {file_path}")
    with path.open("rb") as f:
        return pickle.load(f)


def save_pickle(obj: Any, file_path: str) -> None:
    path = Path(file_path)
    with path.open("wb") as f:
        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)


def ensure_dir_exists(directory: str) -> None:
    Path(directory).mkdir(parents=True, exist_ok=True)


def normalize_vector(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a_norm = normalize_vector(a)
    b_norm = normalize_vector(b)
    return float(np.dot(a_norm, b_norm))


def top_k_indices(similarities: List[float], k: int) -> List[int]:
    if k <= 0:
        raise ValueError("k must be positive")
    return np.argsort(similarities)[-k:][::-1].tolist()


def chunk_list(data: Iterable[Any], size: int) -> List[List[Any]]:
    it = iter(data)
    chunks = []
    while True:
        chunk = list(next(it, None) for _ in range(size))
        if not any(chunk):
            break
        chunks.append([x for x in chunk if x is not None])
    return chunks


def validate_embedding_model(embedding: Embeddings) -> None:
    try:
        embedding.embed_query("test")
    except Exception as e:
        raise ValueError(f"Invalid embedding model: {e}") from e


def build_faiss_index(
    embeddings: List[np.ndarray], ids: List[int]
) -> FAISS:
    if len(embeddings) != len(ids):
        raise ValueError("Embeddings and IDs length mismatch")
    index = FAISS.from_embeddings(np.array(embeddings), embedding=FakeEmbedding(), metadatas=[{"id": i} for i in ids])
    return index


class FakeEmbedding:
    def embed_query(self, text: str) -> np.ndarray:
        raise NotImplementedError

    def embed_documents(self, texts: List[str]) -> List[np.ndarray]:
        raise NotImplementedError


def serialize_vector(vec: np.ndarray) -> bytes:
    return vec.tobytes()


def deserialize_vector(data: bytes, dtype=np.float32, shape=None) -> np.ndarray:
    arr = np.frombuffer(data, dtype=dtype)
    if shape:
        arr = arr.reshape(shape)
    return arr


def load_env_variable(name: str, default: Any = None) -> Any:
    value = os.getenv(name)
    if value is None:
        if default is not None:
            return default
        raise EnvironmentError(f"Environment variable {name} not set")
    return value


def validate_product_data(product: Dict[str, Any]) -> None:
    required_keys = {"id", "title", "description"}
    missing = required_keys - product.keys()
    if missing:
        raise ValueError(f"Missing keys in product data: {missing}")


def get_embedding_cache_path() -> Path:
    cache_dir = os.getenv("EMBEDDING_CACHE_DIR", str(Path(settings.BASE_DIR) / "embedding_cache"))
    ensure_dir_exists(cache_dir)
    return Path(cache_dir) / "embeddings.pkl"


def load_embeddings_from_cache() -> Dict[int, np.ndarray]:
    path = get_embedding_cache_path()
    if not path.is_file():
        return {}
    data: Dict[str, bytes] = load_pickle(path.as_posix())
    return {int(k): deserialize_vector(v) for k, v in data.items()}


def save_embeddings_to_cache(embeddings: Dict[int, np.ndarray]) -> None:
    path = get_embedding_cache_path()
    ensure_dir_exists(path.parent.as_posix())
    serialised = {str(k): serialize_vector(v) for k, v in embeddings.items()}
    save_pickle(serialised, path.as_posix())


def batch_process(
    items: Iterable[Any], func, batch_size: int
) -> List[Any]:
    results = []
    for chunk in chunk_list(items, batch_size):
        results.extend(func(chunk))
    return results


def safe_float(value: Any) -> float:
    try:
        return float(value)
    except Exception as e:
        raise ValueError(f"Cannot convert to float: {value}") from e