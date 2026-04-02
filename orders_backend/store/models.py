from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

import secrets


class UserManager(BaseUserManager):
    """Кастомный менеджер для модели User с аутентификацией по email"""

    def create_user(self, email, password=None, **extra_fields):
        """
        Создает и сохраняет обычного пользователя
        """
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Стандартная модель пользователей + доп. поля
    """
    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'
    email = models.EmailField(verbose_name='email', unique=True)
    first_name = models.CharField(verbose_name='Имя', max_length=40, blank=True)
    last_name = models.CharField(verbose_name='Фамилия', max_length=40, blank=True)
    is_buyer = models.BooleanField(verbose_name='Покупатель', default=False)
    is_supplier = models.BooleanField(verbose_name='Поставщик', default=False)
    username = None
    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email

class Shop(models.Model):
    name = models.CharField(verbose_name='Название магазина', max_length=100)
    user = models.OneToOneField(User, verbose_name='Владелец магазина', on_delete=models.CASCADE)
    is_active = models.BooleanField(verbose_name='Магазин принимает заказы', default=True)
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    filename = models.FileField(verbose_name='Файл', upload_to='shops/', blank=True, null=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(verbose_name='Название категории', max_length=255, unique=True)
    shops = models.ManyToManyField(Shop, verbose_name='Магазины', related_name='categories', blank=True)
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name    


class Product(models.Model):
    name = models.CharField(verbose_name='Название товара', max_length=255)
    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name

# Данные о товаре поставщика
class ProductInfo(models.Model):
    product = models.ForeignKey(Product, verbose_name='Товар', on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', on_delete=models.CASCADE)
    model = models.CharField(verbose_name='Модель/артикул', max_length=255)
    quantity = models.PositiveIntegerField(verbose_name='Количество', default=0, blank=True, null=True)
    price = models.DecimalField(verbose_name='Цена', max_digits=10, default=0, decimal_places=2, blank=True, null=True)
    price_rrc = models.DecimalField(verbose_name='Рекомендуемая розничная цена', max_digits=10, default=0, decimal_places=2, blank=True)
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = 'Информационный список о продуктах'
        constraints = [
            models.UniqueConstraint(fields=['product', 'shop'], name='unique_product_info')
        ]


class Parameter(models.Model):
    name = models.CharField(verbose_name='Название параметра', max_length=255, unique=True)

    class Meta:
        verbose_name = 'Имя параметра'
        verbose_name_plural = 'Имена параметров'

    def __str__(self):
        return self.name

class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте', on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр', on_delete=models.CASCADE)
    value = models.CharField(verbose_name='Значение', max_length=300)

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter')
        ]

class Contact(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    type_contact = models.CharField(verbose_name='Тип', max_length=100)
    value = models.CharField(verbose_name='Значение', max_length=100)

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'

    def __str__(self):
        return self.value

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('canceled', 'Отменен'),
    ]
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    dt = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    status = models.CharField(verbose_name='Статус', max_length=100)
    contact = models.ForeignKey(Contact, verbose_name='Контакт', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ('-dt',)

    def __str__(self):
        return str(self.dt)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Заказ', on_delete=models.CASCADE)
    position = models.ForeignKey(ProductInfo, verbose_name='Товар', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество', default=0, blank=True, null=True)
    price = models.DecimalField(verbose_name='Цена', max_digits=10, default=0, decimal_places=2, blank=True, null=True)

    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = 'Заказанные позиции'

    def __str__(self):
        return str(self.quantity)


class ConfirmEmailToken(models.Model):
    class Meta:
        verbose_name = 'Токен подтверждения Email'
        verbose_name_plural = 'Токены подтверждения Email'

    @staticmethod
    def generate_key():
        """ генерация случайного токена """
        return secrets.token_urlsafe(32)

    user = models.ForeignKey(
        User,
        related_name='confirm_email_tokens',
        on_delete=models.CASCADE,
        verbose_name=_("The User which is associated to this password reset token")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("When was this token generated")
    )

    # Key field, though it is not the primary key of the model
    key = models.CharField(
        _("Key"),
        max_length=64,
        db_index=True,
        unique=True
    )

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)

    def __str__(self):
        return "Password reset token for user {user}".format(user=self.user)


class Cart(models.Model):
    user = models.OneToOneField(User, verbose_name='Покупатель', on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Корзина'
        # verbose_name_plural = 'Корзины'

    def __str__(self):
        return str(self.user)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, verbose_name='Корзина', on_delete=models.CASCADE)
    product_info = models.ForeignKey(ProductInfo, verbose_name='Товар', on_delete=models.CASCADE)
    updated_at = models.DateTimeField(verbose_name='Дата обновления', auto_now=True)
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'cart'], name='unique_product_cart')
    ]