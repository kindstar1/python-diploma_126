from django.shortcuts import render

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from store.serializers import (RegistrationSerializer,ProductInfoSerializer,CartSerializer,ContactSerializer, OrderSerializer)
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny
from store.models import ProductInfo, Cart, CartItem, Contact, Order, OrderItem
from store.filters import ProductInfoFilter
from rest_framework.exceptions import ValidationError

from django.contrib.auth import get_user_model

User = get_user_model()

# Эндпоинт на регистрацию пользователя

class RegistrationView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key, "user": user.id, "email": user.email},
            status=status.HTTP_201_CREATED,
        )

# Эндпоинт по логину по почту

class EmailLoginView(ObtainAuthToken):
    # Кастомный класс для логина по почте
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Неверный email или пароль"}, status=400)

        if not user.check_password(password):
            return Response({"error": "Неверный email или пароль"}, status=400)

        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "user_id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        )

# Эндпоинт по просмотру товаров

class ProductListView(generics.ListAPIView):
    """
    GET /api/products/
    Возвращает список всех товаров с ценами и характеристиками
    """

    queryset = ProductInfo.objects.select_related("product", "shop").prefetch_related(
        "productparameter_set__parameter"
    )
    serializer_class = ProductInfoSerializer
    permission_classes = [AllowAny]
    filterset_class = ProductInfoFilter

# Эндпоинты по управлению корзиной: просмотр, добавление позиций в корзину, удаление, редактирование

# просмотр корзины

class CartView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartSerializer

    def get(self, request, *args, **kwargs):
        user = request.user

        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            cart = Cart.objects.create(user=user)

        serializer = self.get_serializer(cart)

        if cart.cartitem_set.count() == 0:
            return Response({"massage": "Ваша корзина пуста"})
        return Response(serializer.data)

# добавление товаров в корзину

class CartAddView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartSerializer

    def post(self, request, *args, **kwargs):
        user = request.user

        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            cart = Cart.objects.create(user=user)

        product_info_id = request.data.get("product_info_id")
        quantity = request.data.get("quantity", 1)

        try:
            product_info = ProductInfo.objects.get(id=product_info_id)
        except ProductInfo.DoesNotExist:
            return Response({"error": "Такого товара не существует"}, status=404)

        if quantity > product_info.quantity:
            return Response({"error": "К сожалению, товар закончился"}, status=409)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product_info=product_info, defaults={"quantity": quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data)

# удаление товаров из корзины

class CartItemDeleteView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartSerializer
    
    def delete(self, request, *args, **kwargs):
        user = request.user

        id_item = kwargs.get('pk')
        
        try:
            item = CartItem.objects.get(id=id_item, cart__user=user)
        except CartItem.DoesNotExist:
            return Response({"error": "Такого товара нет в корзине"}, status=404)

        cart = item.cart
        item.delete()

        serializer = CartSerializer(cart)
        
        if cart.cartitem_set.count() == 0:
            return Response({"massage": "Ваша корзина пуста"})
        return Response(serializer.data)

# обеовлние товаров в корзине

class CartItemUpdateView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartSerializer

    def patch(self, request, *args, **kwargs):
        user = request.user

        id_item = kwargs.get('pk')
        
        try:
            item = CartItem.objects.get(id=id_item, cart__user=user)
        except CartItem.DoesNotExist:
            return Response({"error": "Такого товара нет в корзине"}, status=404)


        quantity = request.data.get('quantity')
        
        if quantity > item.product_info.quantity:
            return Response({"error": "К сожалению, товар закончился"}, status=409)
        
        
        item.quantity = quantity
        item.save()

        cart = item.cart

        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
# Эндпоинты по управлению контактными данными

# просмотр и создание контакта

class ContactView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ContactSerializer

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ContactSerializer

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)
    
# Эндпоинты по управлению заказами

# Создание заказа

class OrderCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def perform_create(self, serializer):
        user = self.request.user
        contact_id = self.request.data.get('contact_id')

        contact = Contact.objects.get(id=contact_id, user=user)
        cart = Cart.objects.get(user=user)
        cart_items = cart.cartitem_set.all()

        if cart.cartitem_set.count() == 0:
            raise ValidationError({"message": "Ваша корзина пуста"})
        
        order = serializer.save(user=user, status='new', contact=contact)
        
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                position=item.product_info,
                quantity=item.quantity,
                price=item.product_info.price)
        
        cart_items.delete()


class OrderListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        order = Order.objects.filter(user=self.request.user)
        return order

