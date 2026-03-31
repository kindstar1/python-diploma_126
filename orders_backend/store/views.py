from django.shortcuts import render

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from store.serializers import RegistrationSerializer, ProductInfoSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny
from store.models import ProductInfo
from store.filters import ProductInfoFilter


from django.contrib.auth import get_user_model

User = get_user_model()


class RegistrationView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': user.id,
            'email': user.email
        }, status=status.HTTP_201_CREATED)
    
class EmailLoginView(ObtainAuthToken):
    # Кастомный класс для логина по почте
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Неверный email или пароль'},
                status=400
            )
        
        if not user.check_password(password):
            return Response(
                {'error': 'Неверный email или пароль'},
                status=400
            )
        
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        })
    


class ProductListView(generics.ListAPIView):
    """
    GET /api/products/
    Возвращает список всех товаров с ценами и характеристиками
    """
    queryset = ProductInfo.objects.select_related('product', 'shop').prefetch_related('productparameter_set__parameter')
    serializer_class = ProductInfoSerializer
    permission_classes = [AllowAny]
    filterset_class = ProductInfoFilter