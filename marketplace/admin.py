from django.contrib import admin
from django.utils.text import slugify

from .models import Product


class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "category")
    search_fields = ("name", "description")
    list_filter = ("category",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if not obj.slug:
            obj.slug = slugify(obj.name)
        super().save_model(request, obj, form, change)


admin.site.register(Product, ProductAdmin)