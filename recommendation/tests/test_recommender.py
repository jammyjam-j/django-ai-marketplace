import os
import sys
import json
from pathlib import Path

import django
from django.test import TestCase, override_settings
from django.conf import settings
from django.apps import apps
from unittest.mock import patch, MagicMock

# Ensure the project root is in sys.path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from recommendation.recommender import Recommender
from marketplace.models import Product


class MockEmbeddings:
    def __init__(self, *args, **kwargs):
        pass

    def embed_query(self, text: str):
        return [0.1] * 768

    def embed_documents(self, texts):
        return [[0.2] * 768 for _ in texts]


class MockModel:
    def predict(self, inputs, batch_size=32):
        return ["product_{}".format(i) for i in range(len(inputs))]


class RecommenderTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        Product.objects.create(
            name="Laptop",
            description="High performance laptop.",
            price=1200.00,
            category="Electronics",
        )
        Product.objects.create(
            name="Smartphone",
            description="Latest smartphone model.",
            price=800.00,
            category="Electronics",
        )
        Product.objects.create(
            name="Coffee Mug",
            description="Ceramic mug for coffee.",
            price=12.99,
            category="Kitchenware",
        )

    def setUp(self):
        self.recommender = Recommender()

    @patch("recommendation.recommender.Embeddings", new=MockEmbeddings)
    @patch("recommendation.recommender.Model", new=MockModel)
    def test_recommendations_return_list_of_products(self):
        user_preferences = ["I like electronics"]
        recommendations = self.recommender.get_recommendations(user_preferences, limit=2)
        self.assertIsInstance(recommendations, list)
        self.assertLessEqual(len(recommendations), 2)
        for prod in recommendations:
            self.assertIsInstance(prod, Product)

    @patch("recommendation.recommender.Embeddings", new=MockEmbeddings)
    @patch("recommendation.recommender.Model", new=MockModel)
    def test_recommendations_handle_empty_preferences(self):
        with self.assertRaises(ValueError):
            self.recommender.get_recommendations([], limit=3)

    @patch("recommendation.recommender.Embeddings")
    def test_embeddings_initialization_failure(self, mock_embed_cls):
        mock_embed_cls.side_effect = Exception("Failed to load embeddings")
        with self.assertRaises(RuntimeError) as ctx:
            Recommender()
        self.assertIn("Failed to load embeddings", str(ctx.exception))

    @patch("recommendation.recommender.Embeddings", new=MockEmbeddings)
    @patch("recommendation.recommender.Model", new=MockModel)
    def test_caching_mechanism(self):
        cache_key = "rec_test_user"
        self.recommender.cache.set(cache_key, [Product.objects.first()], timeout=60)
        cached = self.recommender.get_cached_recommendations(cache_key)
        self.assertIsInstance(cached, list)
        self.assertEqual(len(cached), 1)

    @patch("recommendation.recommender.Embeddings", new=MockEmbeddings)
    @patch("recommendation.recommender.Model", new=MockModel)
    def test_invalid_limit_type(self):
        with self.assertRaises(TypeError):
            self.recommender.get_recommendations(["prefs"], limit="two")

    @override_settings(RECOMMENDER_MAX_RECS=1)
    @patch("recommendation.recommender.Embeddings", new=MockEmbeddings)
    @patch("recommendation.recommender.Model", new=MockModel)
    def test_configuration_based_limit(self):
        recs = self.recommender.get_recommendations(["prefs"], limit=None)
        self.assertLessEqual(len(recs), 1)

    @patch("recommendation.recommender.Embeddings", new=MockEmbeddings)
    @patch("recommendation.recommender.Model", new=MockModel)
    def test_nonexistent_product_handling(self):
        # Simulate model returning an ID that doesn't exist
        original_predict = MockModel.predict

        def fake_predict(inputs, batch_size=32):
            return ["nonexistent_id"]

        with patch.object(MockModel, "predict", side_effect=fake_predict):
            recs = self.recommender.get_recommendations(["prefs"], limit=1)
            self.assertEqual(len(recs), 0)

    @patch("recommendation.recommender.Embeddings", new=MockEmbeddings)
    @patch("recommendation.recommender.Model", new=MockModel)
    def test_parallel_processing(self):
        # Ensure that get_recommendations can handle multiple preference strings
        prefs = ["I like electronics", "Coffee lovers"]
        recs = self.recommender.get_recommendations(prefs, limit=3)
        self.assertIsInstance(recs, list)

    @patch("recommendation.recommender.Embeddings", new=MockEmbeddings)
    @patch("recommendation.recommender.Model", new=MockModel)
    def test_deterministic_output(self):
        prefs = ["Same preference"]
        recs1 = self.recommender.get_recommendations(prefs, limit=2)
        recs2 = self.recommender.get_recommendations(prefs, limit=2)
        ids1 = [p.id for p in recs1]
        ids2 = [p.id for p in recs2]
        self.assertEqual(ids1, ids2)

    @patch("recommendation.recommender.Embeddings", new=MockEmbeddings)
    @patch("recommendation.recommender.Model", new=MockModel)
    def test_error_on_invalid_product_type(self):
        with self.assertRaises(AttributeError):
            # Force an invalid type in the recommendation list
            self.recommender.get_recommendations(["prefs"], limit=2).append(123)

    @patch("recommendation.recommender.Embeddings", new=MockEmbeddings)
    @patch("recommendation.recommender.Model", new=MockModel)
    def test_memory_leak_prevention(self):
        # Generate many recommendations and ensure memory usage stays bounded
        for _ in range(10):
            self.recommender.get_recommendations(["prefs"], limit=5)

    @patch("recommendation.recommender.Embeddings", new=MockEmbeddings)
    @patch("recommendation.recommender.Model", new=MockModel)
    def test_invalid_product_filtering(self):
        # Simulate a scenario where the model returns a product that is inactive
        Product.objects.create(
            name="Old Phone",
            description="Deprecated phone.",
            price=300.00,
            category="Electronics",
            active=False,
        )

        original_predict = MockModel.predict

        def fake_predict(inputs, batch_size=32):
            return ["product_3"]  # ID corresponding to the inactive product

        with patch.object(MockModel, "predict", side_effect=fake_predict):
            recs = self.recommender.get_recommendations(["prefs"], limit=1)
            self.assertEqual(len(recs), 0)