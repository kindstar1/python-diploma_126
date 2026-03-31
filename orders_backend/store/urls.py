from django.urls import path
from .views import RegistrationView, EmailLoginView, ProductListView

urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register"),
    path("login/", EmailLoginView.as_view(), name="login"),
    path("products/", ProductListView.as_view(), name='products'),
]
