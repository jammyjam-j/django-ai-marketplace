from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductListAPIView, ProductDetailAPIView, ProductCreateAPIView, ProductUpdateAPIView, ProductDeleteAPIView

router = DefaultRouter()
router.register(r'products', ProductListAPIView, basename='product')

urlpatterns = [
    path('', include(router.urls)),
    path('products/<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),
    path('products/create/', ProductCreateAPIView.as_view(), name='product-create'),
    path('products/<int:pk>/update/', ProductUpdateAPIView.as_view(), name='product-update'),
    path('products/<int:pk>/delete/', ProductDeleteAPIView.as_view(), name='product-delete'),
]