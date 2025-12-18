from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'global-discounts', views.GlobalDiscountViewSet, basename='global-discount')
router.register(r'coupons', views.CouponViewSet, basename='coupon')

urlpatterns = [
    path('active/', views.active_global_discounts, name='active-discounts'),
    path('', include(router.urls)),
]
