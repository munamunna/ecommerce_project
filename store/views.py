from django.shortcuts import render

# Create your views here.
# store/views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Cart, CartItem, Product,Category,Review
from .serializers import CartSerializer, CartItemSerializer,ReviewSerializer
from .serializers import CategorySerializer, ProducttSerializer
from rest_framework.permissions import AllowAny
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status

from .models import Order, OrderItem
from .serializers import OrderSerializer

class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_cart(self, user):
        cart, created = Cart.objects.get_or_create(user=user)
        return cart

    def list(self, request):
        cart = self.get_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def create(self, request):
        cart = self.get_cart(request.user)
        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.validated_data['product']
            quantity = serializer.validated_data['quantity']

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, product=product,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            return Response(CartItemSerializer(cart_item).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        cart = self.get_cart(request.user)
        try:
            item = CartItem.objects.get(cart=cart, pk=pk)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)







class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]





class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProducttSerializer
    permission_classes = [AllowAny]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']  #  filter by category ID
    search_fields = ['name', 'description']  #  search by product name or description
    ordering_fields = ['price', 'created_at']  #  sort by price or date




class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        user = request.user
        try:
            cart = Cart.objects.get(user=user, is_active=True)
        except Cart.DoesNotExist:
            return Response({"detail": "No active cart."}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(user=user)

        total = 0
        for item in CartItem.objects.filter(cart=cart):
            price = item.product.price
            quantity = item.quantity
            total += price * quantity
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=quantity,
                price=price
            )

        order.total_amount = total
        order.save()

        # Deactivate cart after checkout
        cart.is_active = False
        cart.save()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)




class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(product=self.request.query_params.get('product'))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
