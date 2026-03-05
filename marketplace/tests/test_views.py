import json
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from marketplace.models import Product

class ProductAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.products = [
            Product.objects.create(
                name=f"Product {i}",
                description="A sample product",
                price=10.0 + i,
                stock=100 - i,
                category="Category A"
            ) for i in range(5)
        ]
        cls.client = APIClient()

    def test_product_list_endpoint(self):
        url = reverse("product-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 5)
        names = [item["name"] for item in data]
        expected_names = [p.name for p in Product.objects.all()]
        self.assertCountEqual(names, expected_names)

    def test_product_detail_endpoint(self):
        product = self.products[0]
        url = reverse("product-detail", args=[product.pk])
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["name"], product.name)
        self.assertEqual(float(data["price"]), float(product.price))
        self.assertEqual(data["stock"], product.stock)

    def test_product_detail_not_found(self):
        url = reverse("product-detail", args=[9999])
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_recommendation_endpoint_valid_product(self):
        product = self.products[1]
        url = reverse("recommendations")
        response = self.client.get(url, {"product_id": product.pk}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 0)

    def test_recommendation_endpoint_invalid_product(self):
        url = reverse("recommendations")
        response = self.client.get(url, {"product_id": 9999}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_product_authenticated(self):
        user = self._create_user()
        self.client.force_authenticate(user=user)
        url = reverse("product-list")
        payload = {
            "name": "New Product",
            "description": "A new item",
            "price": 25.5,
            "stock": 50,
            "category": "Category B"
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["name"], payload["name"])
        self.assertTrue(Product.objects.filter(name=payload["name"]).exists())

    def test_create_product_unauthenticated(self):
        url = reverse("product-list")
        payload = {
            "name": "Unauthorized Product",
            "description": "Should not be created",
            "price": 30.0,
            "stock": 20,
            "category": "Category C"
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def _create_user(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create_user(username="testuser", password="password123")

    def test_update_product_authorized(self):
        user = self._create_user()
        self.client.force_authenticate(user=user)
        product = self.products[2]
        url = reverse("product-detail", args=[product.pk])
        payload = {
            "name": "Updated Name",
            "description": product.description,
            "price": product.price,
            "stock": product.stock,
            "category": product.category
        }
        response = self.client.put(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_product = Product.objects.get(pk=product.pk)
        self.assertEqual(updated_product.name, payload["name"])

    def test_update_product_unauthorized(self):
        product = self.products[3]
        url = reverse("product-detail", args=[product.pk])
        payload = {
            "name": "Malicious Update",
            "description": product.description,
            "price": product.price,
            "stock": product.stock,
            "category": product.category
        }
        response = self.client.put(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_product_authorized(self):
        user = self._create_user()
        self.client.force_authenticate(user=user)
        product = self.products[4]
        url = reverse("product-detail", args=[product.pk])
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())

    def test_delete_product_unauthorized(self):
        product = self.products[0]
        url = reverse("product-detail", args=[product.pk])
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)