from django.contrib import admin
from .models import Order, OrderItem, OrderLog


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('id', 'price_snapshot', 'slicing_info_snapshot', 'subtotal')
    
    def subtotal(self, obj):
        return obj.subtotal if obj.pk else '-'
    subtotal.short_description = 'Subtotal'


class OrderLogInline(admin.TabularInline):
    model = OrderLog
    extra = 0
    readonly_fields = ('id', 'updated_by', 'previous_status', 'new_status', 'notes', 'timestamp')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'total_price', 'assignee', 'creation_date')
    list_filter = ('status', 'creation_date')
    search_fields = ('id', 'customer__user__email', 'tracking_number')
    readonly_fields = ('id', 'ship_snapshot', 'creation_date', 'updated_at')
    inlines = [OrderItemInline, OrderLogInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('id', 'customer', 'status', 'assignee')
        }),
        ('Pricing', {
            'fields': ('total_price',)
        }),
        ('Shipping', {
            'fields': ('ship_snapshot', 'tracking_number')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('creation_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'model', 'material', 'quantity', 'price_snapshot')
    list_filter = ('material',)
    search_fields = ('order__id', 'model__model_name')
    readonly_fields = ('id', 'price_snapshot', 'slicing_info_snapshot')


@admin.register(OrderLog)
class OrderLogAdmin(admin.ModelAdmin):
    list_display = ('order', 'updated_by', 'previous_status', 'new_status', 'timestamp')
    list_filter = ('new_status', 'timestamp')
    search_fields = ('order__id', 'updated_by__employee_name')
    readonly_fields = ('id', 'order', 'updated_by', 'previous_status', 'new_status', 'notes', 'timestamp')
