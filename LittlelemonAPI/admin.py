from django.contrib import admin
from LittlelemonAPI.models import Order, MenuItem, Category, OrderItem, Cart

# Register your models here.

admin.site.register(Cart)
admin.site.register(OrderItem)
admin.site.register(Order)
admin.site.register(MenuItem)
admin.site.register(Category)
