We don't have models content but assume Product with fields id, name, description, price. Provide ListCreateAPIView, RetrieveUpdateDestroyAPIView, and a recommendation view that uses recommendation.recommender.Recommender to get recommendations. Use pagination. Implement error handling for invalid product id. Use @api_view. Let's write.from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework.exceptions import ValidationError

from .models import Product
from .serializers import ProductSerializer
from recommendation.recommender import Recommender


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            return Response({"errors": exc.detail}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            return Response({"errors": exc.detail}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductRecommendationView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk=None):
        if pk is None:
            return Response({"detail": "Product ID required."}, status=status.HTTP_400_BAD_REQUEST)
        product = get_object_or_404(Product, pk=pk)
        recommender = Recommender()
        try:
            recommendations = recommender.get_recommendations(product.id)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if not isinstance(recommendations, list):
            return Response({"detail": "Invalid recommendation format."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        serializer = ProductSerializer(recommendations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)