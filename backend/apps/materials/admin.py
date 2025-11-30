from django.contrib import admin
from .models import Material, CartItem


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'density_g_cm3', 'price_twd_g', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('customer', 'model', 'material', 'quantity', 'created_at')
    list_filter = ('material', 'created_at')
    search_fields = ('customer__user__email', 'model__model_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
