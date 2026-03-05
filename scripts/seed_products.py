We need to read product model.#!/usr/bin/env python
import os
import sys
from pathlib import Path

try:
    from django.core.management import setup_environ
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    import django
    django.setup()
except Exception as exc:
    print(f"Failed to set up Django environment: {exc}", file=sys.stderr)
    sys.exit(1)

from marketplace.models import Product
from faker import Faker

def seed_products(count):
    fake = Faker()
    created = 0
    for _ in range(count):
        name = fake.unique.catch_phrase()
        description = fake.text(max_nb_chars=200)
        price = round(fake.pydecimal(left_digits=3, right_digits=2, positive=True), 2)
        stock = fake.random_int(min=0, max=100)
        try:
            product, created_flag = Product.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'price': price,
                    'stock': stock
                }
            )
            if created_flag:
                created += 1
        except Exception as e:
            print(f"Error creating product {name}: {e}", file=sys.stderr)
    return created

def main():
    try:
        count = int(os.getenv('NUM_PRODUCTS', '10'))
    except ValueError:
        print("NUM_PRODUCTS must be an integer", file=sys.stderr)
        sys.exit(1)

    if Product.objects.exists():
        print("Products already exist. Skipping seeding.")
        return

    created = seed_products(count)
    print(f"Seeded {created} products.")

if __name__ == "__main__":
    main()