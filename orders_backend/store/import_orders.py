from django.db import transaction
import yaml
from store.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter
from django.contrib.auth import get_user_model

def import_orders(file_path, user_id):
    user = get_user_model().objects.get(id=user_id)
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        with transaction.atomic():
            # Если любая из этих операций вызовет ошибку, откатываем изменения
            shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=user.id)
            category_mapping = {}
            for category in data['categories']:
                category_obj, _ = Category.objects.get_or_create(name=category['name'])
                category_mapping[category['id']] = category_obj
                category_obj.shops.add(shop)
            for product in data['goods']:
                category_obj = category_mapping[product['category']]
                product_obj, _ = Product.objects.get_or_create(
                    name=product['name'],
                    category=category_obj,
                )
                product_info, _ = ProductInfo.objects.update_or_create(
                    product=product_obj,
                    shop=shop,
                    defaults={
                        'model': product['model'],
                        'quantity': product['quantity'],
                        'price': product['price'],
                        'price_rrc': product['price_rrc'],
                    },
                )
                for param_name, param_value in product['parameters'].items():
                    parameter_obj, _ = Parameter.objects.get_or_create(name=param_name)

                    ProductParameter.objects.update_or_create(
                        product_info=product_info,
                        parameter=parameter_obj,
                        defaults={'value': str(param_value)}
                    )
