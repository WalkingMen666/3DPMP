from django.contrib import admin
from .models import ShippingOption, SavedAddress


@admin.register(ShippingOption)
class ShippingOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'base_fee', 'is_active', 'updated_at')
    list_filter = ('type', 'is_active')
    search_fields = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(SavedAddress)
class SavedAddressAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer', 'address_type', 'is_default', 'created_at')
    list_filter = ('address_type', 'is_default')
    search_fields = ('name', 'customer__user__email', 'address_details')
    readonly_fields = ('id', 'created_at', 'updated_at')
