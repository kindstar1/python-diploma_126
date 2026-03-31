from django_filters import rest_framework as filters
from .models import ProductInfo

class ProductInfoFilter(filters.FilterSet):
    category = filters.NumberFilter(field_name='product__category__id')
    shop = filters.NumberFilter(field_name='shop__id')
    price_min = filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = filters.NumberFilter(field_name='price', lookup_expr='lte')
    search = filters.CharFilter(field_name='product__name', lookup_expr='icontains')
    
    class Meta:
        model = ProductInfo
        fields = ['category', 'shop', 'price_min', 'price_max', 'search']