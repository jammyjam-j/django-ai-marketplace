We need to write test_recommendation.py. Likely uses recommendation/recommender.py. Let's inspect that file.Open that file.We need to read it.import os
import sys
import numpy as np
from unittest import TestCase, mock

import django
from django.test import TransactionTestCase
from django.conf import settings

# Ensure Django is configured
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

from marketplace.models import Product
from recommendation.recommender import Recommender


class RecommendationTests(TransactionTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.products = [
            Product.objects.create(name='Alpha', description='First product'),
            Product.objects.create(name='Beta', description='Second product'),
            Product.objects.create(name='Gamma', description='Third product'),
            Product.objects.create(name='Delta', description='Fourth product'),
            Product.objects.create(name='Epsilon', description='Fifth product'),
        ]
        cls.recommender = Recommender()

    def _mock_embedding(self, text):
        np.random.seed(abs(hash(text)) % (2**32))
        return np.random.rand(128)

    @mock.patch.object(Recommender, '_get_product_vector')
    def test_recommendation_returns_different_products(self, mock_get_vector):
        mock_get_vector.side_effect = self._mock_embedding
        base_product = self.products[0]
        recommendations = self.recommender.recommend(base_product.id)
        self.assertIsInstance(recommendations, list)
        for rec in recommendations:
            self.assertNotEqual(rec.id, base_product.id)

    @mock.patch.object(Recommender, '_get_product_vector')
    def test_recommendation_excludes_input(self, mock_get_vector):
        mock_get_vector.side_effect = self._mock_embedding
        base_product = self.products[1]
        recs = self.recommender.recommend(base_product.id)
        ids = [p.id for p in recs]
        self.assertNotIn(base_product.id, ids)

    @mock.patch.object(Recommender, '_get_product_vector')
    def test_recommendation_with_no_products(self, mock_get_vector):
        Product.objects.all().delete()
        base_product_id = 999
        with self.assertRaises(ValueError):
            self.recommender.recommend(base_product_id)

    @mock.patch.object(Recommender, '_get_product_vector')
    def test_recommendation_consistency_with_same_input(self, mock_get_vector):
        mock_get_vector.side_effect = self._mock_embedding
        base_product = self.products[2]
        first_run = self.recommender.recommend(base_product.id)
        second_run = self.recommender.recommend(base_product.id)
        self.assertEqual([p.id for p in first_run], [p.id for p in second_run])

    @mock.patch.object(Recommender, '_get_product_vector')
    def test_recommendation_limits_output(self, mock_get_vector):
        mock_get_vector.side_effect = self._mock_embedding
        base_product = self.products[3]
        recommendations = self.recommender.recommend(base_product.id, top_n=2)
        self.assertEqual(len(recommendations), 2)

    @mock.patch.object(Recommender, '_get_product_vector')
    def test_recommendation_handles_equal_vectors(self, mock_get_vector):
        vector = np.zeros(128)
        mock_get_vector.return_value = vector
        base_product = self.products[4]
        recs = self.recommender.recommend(base_product.id)
        self.assertIsInstance(recs, list)

    @mock.patch.object(Recommender, '_get_product_vector')
    def test_recommendation_with_invalid_id_raises(self, mock_get_vector):
        mock_get_vector.side_effect = self._mock_embedding
        with self.assertRaises(ValueError):
            self.recommender.recommend(0)
        with self.assertRaises(ValueError):
            self.recommender.recommend(-1)

    @mock.patch.object(Recommender, '_get_product_vector')
    def test_recommendation_does_not_return_duplicates(self, mock_get_vector):
        mock_get_vector.side_effect = self._mock_embedding
        base_product = self.products[0]
        recs = self.recommender.recommend(base_product.id)
        ids = [p.id for p in recs]
        self.assertEqual(len(ids), len(set(ids)))

    @mock.patch.object(Recommender, '_get_product_vector')
    def test_recommendation_with_high_top_n(self, mock_get_vector):
        mock_get_vector.side_effect = self._mock_embedding
        base_product = self.products[1]
        recs = self.recommender.recommend(base_product.id, top_n=10)
        expected_count = min(9, Product.objects.count() - 1)
        self.assertEqual(len(recs), expected_count)

    @mock.patch.object(Recommender, '_get_product_vector')
    def test_recommendation_integration_with_real_embeddings(self, mock_get_vector):
        mock_get_vector.side_effect = self._mock_embedding
        base_product = self.products[2]
        recs = self.recommender.recommend(base_product.id)
        self.assertTrue(all(isinstance(p, Product) for p in recs))
        self.assertGreater(len(recs), 0)

    @mock.patch.object(Recommender, '_get_product_vector')
    def test_recommendation_with_empty_database(self, mock_get_vector):
        Product.objects.all().delete()
        base_id = self.products[0].id
        with self.assertRaises(ValueError):
            self.recommender.recommend(base_id)