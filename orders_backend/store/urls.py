from django.urls import path
from .views import (
    RegistrationView,
    EmailLoginView,
    ProductListView,
    CartItemUpdateView, CartItemDeleteView, CartAddView, CartView,
    ContactDetailView, ContactView,
    OrderListView, OrderCreateView
)

urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register"),
    path("login/", EmailLoginView.as_view(), name="login"),
    path("products/", ProductListView.as_view(), name="products"),
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/add", CartAddView.as_view(), name="cart-add"),
    path("cart/<int:pk>/", CartItemDeleteView.as_view(), name="cart-item-delete"),
    path("cart/update/<int:pk>/", CartItemUpdateView.as_view(), name="cart-item-update"),
    path("contacts/", ContactView.as_view(), name="contacts"),
    path("contacts/<int:pk>/", ContactDetailView.as_view(), name="contact-detail"),
    path('orders/', OrderListView.as_view(), name='orders'),
    path('orders/create/', OrderCreateView.as_view(), name='orders-create'),
]
