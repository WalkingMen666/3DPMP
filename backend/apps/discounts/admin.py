from django.contrib import admin
from .models import Discount, GlobalDiscount, Coupon, IsAffected, CouponRedemption


class GlobalDiscountInline(admin.StackedInline):
    model = GlobalDiscount
    can_delete = False
    verbose_name = 'Global Discount Settings'
    verbose_name_plural = 'Global Discount Settings'


class CouponInline(admin.StackedInline):
    model = Coupon
    can_delete = False
    verbose_name = 'Coupon Settings'
    verbose_name_plural = 'Coupon Settings'


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_type', 'is_fixed', 'dis_value', 'works_on', 'is_active', 'start_date', 'due_date')
    list_filter = ('is_fixed', 'works_on', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at', 'discount_type')
    inlines = [GlobalDiscountInline, CouponInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'name', 'description', 'is_active')
        }),
        ('Validity Period', {
            'fields': ('start_date', 'due_date')
        }),
        ('Discount Rules', {
            'fields': ('works_on', 'is_fixed', 'dis_value', 'min_price', 'max_discount')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GlobalDiscount)
class GlobalDiscountAdmin(admin.ModelAdmin):
    list_display = ('discount', 'priority', 'is_active', 'start_date', 'due_date')
    list_filter = ('discount__is_active', 'priority')
    search_fields = ('discount__name',)
    
    def is_active(self, obj):
        return obj.discount.is_active
    is_active.boolean = True
    is_active.short_description = 'Active'
    
    def start_date(self, obj):
        return obj.discount.start_date
    
    def due_date(self, obj):
        return obj.discount.due_date


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('coupon_code', 'discount', 'max_uses_total', 'max_uses_per_customer', 'total_redemptions', 'is_active')
    list_filter = ('discount__is_active',)
    search_fields = ('coupon_code', 'discount__name')
    
    def is_active(self, obj):
        return obj.discount.is_active
    is_active.boolean = True
    is_active.short_description = 'Active'


@admin.register(IsAffected)
class IsAffectedAdmin(admin.ModelAdmin):
    list_display = ('order', 'global_discount', 'discount_amount', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('order__id', 'global_discount__discount__name')
    readonly_fields = ('id', 'order', 'global_discount', 'discount_snapshot_info', 'discount_amount', 'created_at')


@admin.register(CouponRedemption)
class CouponRedemptionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'coupon', 'order', 'discount_amount', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('customer__user__email', 'coupon__coupon_code', 'order__id')
    readonly_fields = ('id', 'customer', 'coupon', 'order', 'discount_snapshot_info', 'discount_amount', 'timestamp')
