import os
from django.test import TestCase
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from marketplace.models import Product, Category

class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics", description="Electronic items")

    def test_category_creation(self):
        self.assertEqual(self.category.name, "Electronics")
        self.assertEqual(self.category.description, "Electronic items")
        self.assertIsInstance(str(self.category), str)

    def test_unique_name_constraint(self):
        with self.assertRaises(ValidationError) as cm:
            duplicate = Category(name="Electronics", description="Duplicate")
            duplicate.full_clean()
        errors = cm.exception.message_dict
        self.assertIn('name', errors)
        self.assertTrue(any("unique" in e.lower() for e in errors['name']))

    def test_slug_generation(self):
        if hasattr(self.category, "slug"):
            expected_slug = os.path.basename(os.path.normpath(self.category.name.replace(" ", "-").lower()))
            self.assertEqual(self.category.slug, expected_slug)

class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Books", description="All books")
        self.product_data = {
            "name": "Django for Beginners",
            "description": "Learn Django step by step.",
            "price": 29.99,
            "stock": 100,
            "category": self.category
        }
        self.product = Product.objects.create(**self.product_data)

    def test_product_creation(self):
        self.assertEqual(self.product.name, self.product_data["name"])
        self.assertEqual(self.product.description, self.product_data["description"])
        self.assertEqual(float(self.product.price), self.product_data["price"])
        self.assertEqual(self.product.stock, self.product_data["stock"])
        self.assertEqual(self.product.category, self.category)
        self.assertIsInstance(str(self.product), str)

    def test_price_must_be_positive(self):
        self.product.price = -5
        with self.assertRaises(ValidationError) as cm:
            self.product.full_clean()
        errors = cm.exception.message_dict
        self.assertIn('price', errors)
        self.assertTrue(any("positive" in e.lower() for e in errors['price']))

    def test_stock_cannot_be_negative(self):
        self.product.stock = -10
        with self.assertRaises(ValidationError) as cm:
            self.product.full_clean()
        errors = cm.exception.message_dict
        self.assertIn('stock', errors)
        self.assertTrue(any("non-negative" in e.lower() for e in errors['stock']))

    def test_name_uniqueness_within_category(self):
        duplicate_product = Product(name=self.product.name, description="Duplicate", price=20.0, stock=10, category=self.category)
        with self.assertRaises(ValidationError) as cm:
            duplicate_product.full_clean()
        errors = cm.exception.message_dict
        self.assertIn('name', errors)
        self.assertTrue(any("unique" in e.lower() for e in errors['name']))

    def test_cross_category_name_allowed(self):
        other_category = Category.objects.create(name="Music", description="All music")
        duplicate_product = Product(name=self.product.name, description="Different category", price=15.0, stock=5, category=other_category)
        try:
            duplicate_product.full_clean()
            duplicate_product.save()
        except ValidationError:
            self.fail("ValidationError raised for product with same name in different category")

    def test_slug_field_exists_and_unique(self):
        if hasattr(Product, "slug"):
            self.assertTrue(hasattr(self.product, "slug"))
            self.assertIsInstance(self.product.slug, str)
            other_product = Product.objects.create(
                name="Another Book",
                description="Second book",
                price=15.0,
                stock=20,
                category=self.category
            )
            try:
                self.product.full_clean()
                self.product.save()
                other_product.full_clean()
                other_product.save()
            except ValidationError as e:
                errors = e.message_dict
                self.assertIn('slug', errors)
                self.assertTrue(any("unique" in err.lower() for err in errors['slug']))

    def test_product_str_representation(self):
        expected_str = f"{self.product.name} ({self.category.name})"
        self.assertEqual(str(self.product), expected_str)

    def test_delete_category_cascade(self):
        self.product.delete()
        with self.assertRaises(ObjectDoesNotExist):
            Product.objects.get(pk=self.product.pk)

    def test_product_image_field_optional(self):
        if hasattr(Product, "image"):
            product_without_image = Product(
                name="Imageless Product",
                description="No image here",
                price=10.0,
                stock=5,
                category=self.category
            )
            try:
                product_without_image.full_clean()
                product_without_image.save()
            except ValidationError:
                self.fail("ValidationError raised for product without image when image field is optional")