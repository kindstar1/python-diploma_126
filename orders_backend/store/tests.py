from django.test import override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from store.models import (
    Shop,
    Category,
    Product,
    ProductInfo,
    Cart,
    Contact,
    Order,
)

User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="test@example.com",
)
class RegistrationAPITest(APITestCase):
    def test_register_returns_201_and_token(self):
        r = self.client.post(
            "/api/v1/register/",
            {
                "email": "buyer_new@example.com",
                "password": "Xk9#mP2$vLqW",
                "first_name": "Ivan",
                "last_name": "Petrov",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        self.assertIn("token", r.data)
        self.assertTrue(User.objects.filter(email="buyer_new@example.com").exists())


class LoginAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="login@example.com",
            password="SecretPass1!",
            first_name="A",
            last_name="B",
        )

    def test_login_returns_token(self):
        r = self.client.post(
            "/api/v1/login/",
            {"email": "login@example.com", "password": "SecretPass1!"},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("token", r.data)


class ProductListAPITest(APITestCase):
    def test_products_list_200(self):
        r = self.client.get("/api/v1/products/")
        self.assertEqual(r.status_code, 200)


class CartAddAPITest(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(
            email="cart@example.com",
            password="p",
            first_name="a",
            last_name="b",
        )
        self.token = Token.objects.create(user=self.buyer)
        seller = User.objects.create_user(
            email="seller@example.com",
            password="p",
            first_name="s",
            last_name="s",
        )
        shop = Shop.objects.create(name="S1", user=seller)
        cat = Category.objects.create(name="C1")
        prod = Product.objects.create(name="P1", category=cat)
        self.pi = ProductInfo.objects.create(
            product=prod,
            shop=shop,
            model="m1",
            quantity=100,
            price="99.50",
            price_rrc="100.00",
        )

    def test_cart_add_requires_auth(self):
        r = self.client.post(
            "/api/v1/cart/add",
            {"product_info_id": self.pi.id, "quantity": 1},
            format="json",
        )
        self.assertEqual(r.status_code, 401)

    def test_cart_add_creates_item(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        r = self.client.post(
            "/api/v1/cart/add",
            {"product_info_id": self.pi.id, "quantity": 3},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        cart = Cart.objects.get(user=self.buyer)
        self.assertEqual(cart.cartitem_set.count(), 1)
        self.assertEqual(cart.cartitem_set.first().quantity, 3)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="test@example.com",
)
class OrderCreateAPITest(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(
            email="order@example.com",
            password="p",
            first_name="a",
            last_name="b",
        )
        self.token = Token.objects.create(user=self.buyer)
        seller = User.objects.create_user(
            email="order_seller@example.com",
            password="p",
            first_name="s",
            last_name="s",
        )
        shop = Shop.objects.create(name="S2", user=seller)
        cat = Category.objects.create(name="C2")
        prod = Product.objects.create(name="P2", category=cat)
        pi = ProductInfo.objects.create(
            product=prod,
            shop=shop,
            model="m2",
            quantity=50,
            price="10.00",
            price_rrc="12.00",
        )
        cart, _ = Cart.objects.get_or_create(user=self.buyer)
        cart.cartitem_set.create(product_info=pi, quantity=2)
        self.contact = Contact.objects.create(
            user=self.buyer,
            type_contact="address",
            value="Moscow",
        )

    def test_order_create_empties_cart(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        r = self.client.post(
            "/api/v1/orders/create/",
            {"contact_id": self.contact.id},
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Order.objects.filter(user=self.buyer).count(), 1)
        cart = Cart.objects.get(user=self.buyer)
        self.assertEqual(cart.cartitem_set.count(), 0)
        order = Order.objects.get(user=self.buyer)
        self.assertEqual(order.orderitem_set.count(), 1)
