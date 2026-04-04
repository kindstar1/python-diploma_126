from rest_framework import serializers
from django.contrib.auth import get_user_model
from store.models import ProductInfo, ProductParameter, CartItem, Cart, Contact, OrderItem, Order

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
    name = serializers.CharField(source="parameter.name", read_only=True)

    class Meta:
        model = ProductParameter
        fields = ["name", "value"]


class ProductInfoSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    shop_sup = serializers.CharField(source="shop.name", read_only=True)
    params = ProductParameterSerializer(
        source="productparameter_set", many=True, read_only=True
    )

    class Meta:
        model = ProductInfo
        fields = ["product_name", "model", "shop_sup", "price", "quantity", "params"]


class CartProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="product_info.product.name", read_only=True)
    shop = serializers.CharField(source="product_info.shop.name", read_only=True)
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        source="product_info.price",
        read_only=True,
    )
    quantity = serializers.IntegerField(read_only=True)

    amount = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["name", "shop", "price", "quantity", "amount"]

    def get_amount(self, obj):
        price = obj.product_info.price
        quantity = obj.quantity
        return price * quantity


class CartSerializer(serializers.ModelSerializer):
    items = CartProductSerializer(source="cartitem_set", many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["items", "total_amount"]

    def get_total_amount(self, obj):
        total_amount = 0
        for i in obj.cartitem_set.all():
            total_amount += i.product_info.price * i.quantity
        return total_amount

class ContactSerializer(serializers.ModelSerializer):

    def validate(self, data):
        user = self.context['request'].user
        type_contact = data.get('type_contact')

        if type_contact == 'phone':
            tel = Contact.objects.filter(user=user, type_contact='phone')
            if tel.count() >= 1:
                raise serializers.ValidationError("Phone number already exists")
            
        elif type_contact == 'address':
            adress = Contact.objects.filter(user=user, type_contact='address')
            if adress.count() >= 5:
                    raise serializers.ValidationError("Количество возможностей добавить адресс превышено")
        return data

    class Meta:
        model = Contact
        fields = ["id", "type_contact", "value"]

class OrderItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="product_info.product.name", read_only=True)
    shop = serializers.CharField(source="product_info.shop.name", read_only=True)
    amount = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['name', 'shop', 'price', 'quantity', 'amount']
    
    def get_amount(self, obj):
        return obj.price * obj.quantity
    
class OrderSerializer(serializers.ModelSerializer):
    
    items = OrderItemSerializer(source="orderitem_set", many=True, read_only=True)
    total_sum = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'status', 'dt', 'contact', 'items', 'total_sum']

    def get_total_sum(self, obj):
        total_sum = 0
        for i in obj.orderitem_set.all():
            total_sum += i.price * i.quantity
        return total_sum