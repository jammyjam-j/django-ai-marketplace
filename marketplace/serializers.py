from rest_framework import serializers
from django.core.exceptions import ValidationError

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for the Product model.
    """

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "description",
            "price",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_price(self, value):
        """
        Ensure the price is non-negative.
        """
        if value < 0:
            raise serializers.ValidationError("Price must be a positive number.")
        return value

    def create(self, validated_data):
        """
        Create and return a new Product instance.
        """
        try:
            product = Product.objects.create(**validated_data)
        except Exception as exc:
            raise ValidationError(f"Failed to create product: {exc}") from exc
        return product

    def update(self, instance, validated_data):
        """
        Update and return an existing Product instance.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        try:
            instance.save()
        except Exception as exc:
            raise ValidationError(f"Failed to update product: {exc}") from exc
        return instance

    def validate(self, attrs):
        """
        Cross-field validation can be added here.
        """
        if "name" in attrs and not attrs["name"].strip():
            raise serializers.ValidationError({"name": "Name cannot be empty."})
        return attrs


class ProductDetailSerializer(ProductSerializer):
    """
    Serializer used for detailed product views, potentially including additional
    computed fields or related data.
    """

    class Meta(ProductSerializer.Meta):
        pass

    def to_representation(self, instance):
        """
        Extend the default representation with custom logic if necessary.
        """
        rep = super().to_representation(instance)
        # Example: add a formatted price string
        rep["price_formatted"] = f"${rep['price']:.2f}"
        return rep

    def validate_name(self, value):
        """
        Ensure product name is unique within the database.
        """
        if Product.objects.filter(name=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("Product with this name already exists.")
        return value

    def update(self, instance, validated_data):
        """
        Override to include custom validation logic for updates.
        """
        if "name" in validated_data:
            # Prevent changing the name to an existing product's name
            self.validate_name(validated_data["name"])
        return super().update(instance, validated_data)