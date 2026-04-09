import logging

from django.shortcuts import render

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from store.serializers import (RegistrationSerializer,ProductInfoSerializer,CartSerializer,ContactSerializer, OrderSerializer, OrderStatusSerializer)
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny
from store.models import ProductInfo, Cart, CartItem, Contact, Order, OrderItem, ConfirmEmailToken
from store.filters import ProductInfoFilter
from rest_framework.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from rest_framework.views import APIView

from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger('store.views')

# рачет суммы заказа для отправки письма 

def calculate_order_total(order):
    total = 0
    for item in order.orderitem_set.all():
        total += item.price * item.quantity
    return total

# Эндпоинт на регистрацию пользователя

class RegistrationView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        email_token = ConfirmEmailToken.objects.create(user=user)
        confirm_url = request.build_absolute_uri(reverse('confirm-email') + f'?token={email_token.key}')
        send_mail(
            subject='Подтверждение регистрации',
            message=f'Для подтверждения email перейдите по ссылке: {confirm_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        token, created = Token.objects.get_or_create(user=user)
        logger.info('Регистрация: user_id=%s email=%s', user.id, user.email)
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
        logger.info('Вход: user_id=%s', user.id)
        return Response(
            {
                "token": token.key,
                "user_id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        )


class ConfirmEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token_key = request.query_params.get('token')
        
        if not token_key:
            return Response({"error": "Токен не предоставлен"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = ConfirmEmailToken.objects.get(key=token_key)
        except ConfirmEmailToken.DoesNotExist:
            return Response({"error": "Неверный или истекший токен"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = token.user
        user.is_active = True
        user.save()
        
        token.delete()
        logger.info('Подтверждение email: user_id=%s', user.id)
        return Response({"message": "Email успешно подтвержден"}, status=status.HTTP_200_OK)

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

class ProductDetailView(generics.RetrieveAPIView):
    queryset = ProductInfo.objects.select_related("product", "shop").prefetch_related(
        "productparameter_set__parameter"
    )
    serializer_class = ProductInfoSerializer
    permission_classes = [AllowAny]

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
        logger.info(
            'Корзина: user_id=%s product_info_id=%s qty=%s',
            user.id,
            product_info_id,
            cart_item.quantity,
        )
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

        total_sum = calculate_order_total(order)
        logger.info('Заказ создан: order_id=%s user_id=%s sum=%s', order.id, user.id, total_sum)

        send_mail(
            subject=f'Заказ №{order.id} подтвержден',
            message=f'Ваш заказ №{order.id} успешно создан. Сумма: {total_sum} руб.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
)
        admin_email = get_user_model().objects.filter(is_staff=True).values_list('email', flat=True)

        if admin_email:
            send_mail(
                subject=f'Новый заказ №{order.id}',
                message=f'Поступил новый заказ №{order.id} от {user.email} на сумму {total_sum} руб.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(admin_email),
                fail_silently=False,
            )

# Просмотр заказов
class OrderListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        order = Order.objects.filter(user=self.request.user)
        return order

# Просмотр конкретного заказа
class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

# Изменение статусов поставиком

class OrderStatusUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderStatusSerializer
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        pk = kwargs.get('pk')

        order = self.get_object()

        if not request.user.is_supplier:
            return Response({"error": "Доступ только для поставщиков"}, status=403)
        has_supplier_items = order.orderitem_set.filter(position__shop__user=request.user).exists()

        if not has_supplier_items:
            return Response({"error": "В этом заказе нет ваших товаров"}, status=403)

        response = super().update(request, *args, **kwargs)
        if getattr(response, 'status_code', 500) < 400:
            logger.info(
                'Статус заказа: order_id=%s supplier_user_id=%s new_status=%s',
                order.id,
                request.user.id,
                request.data.get('status', ''),
            )
        return response
