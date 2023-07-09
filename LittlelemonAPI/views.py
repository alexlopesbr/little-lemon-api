from decimal import Decimal

from django.db import transaction
from django.contrib.auth.models import Group, User
from django.db.models import Q

from rest_framework import generics, viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


from .models import Cart, Category, MenuItem, Order, OrderItem
from .serializers import (
    CartSerializer,
    CategorySerializer,
    MenuItemSerializer,
    OrdersSerializer,
    UserSerializer,
)

from .throttles import TenCallPerMinute


class MenuItemView(generics.ListAPIView, generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    ordering_fields = ['price']
    search_fields = ['title', 'category__title']

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.query_params.get('search', None)

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | Q(category__title__icontains=search_query)
            )
        return queryset

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [AllowAny()]


class SingleItemView(generics.RetrieveUpdateDestroyAPIView, generics.RetrieveAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ManagerUsersView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        manager_group = Group.objects.get(name='Manager')
        queryset = User.objects.filter(groups=manager_group)
        return queryset

    def perform_create(self, serializer):
        manager_group = Group.objects.get(name='Manager')
        user = serializer.save()
        user.groups.add(manager_group)


class ManagerSingleUserView(generics.RetrieveDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        manager_group = Group.objects.get(name='Manager')
        queryset = User.objects.filter(groups=manager_group)
        return queryset


class DeliveryCrewManagement(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        delivery_group = Group.objects.get(name='Delivery Crew')
        queryset = User.objects.filter(groups=delivery_group)
        return queryset

    def perform_create(self, serializer):
        delivery_group = Group.objects.get(name='Delivery Crew')
        user = serializer.save()
        user.groups.add(delivery_group)


class DeliveryCrewManagementSingleView(generics.RetrieveDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        delivery_group = Group.objects.get(name='Delivery Crew')
        queryset = User.objects.filter(groups=delivery_group)
        return queryset


class CartView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Cart.objects.filter(user=user)

    def perform_create(self, serializer):
        menu_item = self.request.data.get('menu_item')
        quantity = self.request.data.get('quantity')
        item_price = MenuItem.objects.get(pk=menu_item).price
        quantity = int(quantity)
        price = quantity * item_price
        serializer.save(user=self.request.user, price=price)

    @api_view(['DELETE'])
    def delete(self, request):
        Cart.objects.filter(user=self.request.user).delete()
        return Response.no_content()


class OrdersView(generics.ListCreateAPIView):
    serializer_class = OrdersSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle, TenCallPerMinute]

    def perform_create(self, serializer):
        cart_items = Cart.objects.filter(user=self.request.user)
        total = self.calculate_total(cart_items)
        order = serializer.save(user=self.request.user, total=total)

        order_items = [
            OrderItem(
                order=order,
                menu_item=cart_item.menu_item,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                price=cart_item.price,
            )
            for cart_item in cart_items
        ]

        with transaction.atomic():
            OrderItem.objects.bulk_create(order_items)

        cart_items.delete()

    def get_queryset(self):
        user = self.request.user

        if user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def calculate_total(self, cart_items):
        total = Decimal(0)
        for item in cart_items:
            total += item.price
        return total


class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrdersSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [TenCallPerMinute]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        return Order.objects.filter(user=user)
