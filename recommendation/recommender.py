We need to view utils.import os
import json
import logging
from typing import List, Dict, Any

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from marketplace.models import Product

logger = logging.getLogger(__name__)

class Recommender:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ImproperlyConfigured("OPENAI_API_KEY is missing in environment.")
        self.endpoint = "https://api.openai.com/v1/embeddings"
        self.model_name = "text-embedding-ada-002"
        self._product_embeddings: Dict[int, List[float]] = {}

    def _fetch_embedding(self, text: str) -> List[float]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {"input": text, "model": self.model_name}
        response = requests.post(self.endpoint, headers=headers, json=payload)
        if response.status_code != 200:
            raise RuntimeError(
                f"Embedding request failed: {response.status_code} {response.text}"
            )
        data = response.json()
        return data["data"][0]["embedding"]

    def _ensure_embeddings_loaded(self) -> None:
        if not self._product_embeddings:
            products = Product.objects.all()
            for product in products:
                combined_text = f"{product.name}. {product.description}"
                try:
                    embedding = self._fetch_embedding(combined_text)
                except Exception as exc:
                    logger.error(
                        f"Failed to fetch embedding for product {product.id}: {exc}"
                    )
                    continue
                self._product_embeddings[product.id] = embedding

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = sum(a * a for a in vec1) ** 0.5
        norm_b = sum(b * b for b in vec2) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def recommend(self, product_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        self._ensure_embeddings_loaded()
        target_embedding = self._product_embeddings.get(product_id)
        if not target_embedding:
            raise ValueError(f"No embedding found for product {product_id}")
        similarities = []
        for pid, emb in self._product_embeddings.items():
            if pid == product_id:
                continue
            score = self._cosine_similarity(target_embedding, emb)
            similarities.append((pid, score))
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_ids = [pid for pid, _ in similarities[:limit]]
        return list(Product.objects.filter(id__in=top_ids).values("id", "name", "description", "price"))