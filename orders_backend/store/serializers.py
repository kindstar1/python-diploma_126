from rest_framework import serializers
from django.contrib.auth import get_user_model
from store.models import ProductInfo, Parameter, ProductParameter

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name"]

    def validate_email(self, data):
        if User.objects.filter(email=data).exists():
            raise serializers.ValidationError("Email already exists")
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        return user

class ProductParameterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='parameter.name', read_only=True)

    class Meta:
        model = ProductParameter
        fields = ['name', 'value']


class ProductInfoSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    shop_sup = serializers.CharField(source='shop.name',read_only=True)
    params = ProductParameterSerializer(source='productparameter_set', many=True, read_only=True)

    class Meta:
        model = ProductInfo
        fields = ['product_name', 'model', 'shop_sup', 'price', 'quantity', 'params']
