from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    InventoryView, InventoryGroupView, ShopView, InvoiceView, SummaryView, TopSellingView,
    SaleByShopView, PurchaseView, InventoryCSVLoaderView
)


router = DefaultRouter(trailing_slash=False)

router.register('inventory', InventoryView, basename='inventory')
router.register('group', InventoryGroupView, basename='group')
router.register('shop', ShopView, basename='shop')
router.register('invoice', InvoiceView, basename='invoice')
router.register('summary', SummaryView, basename='summary')
router.register('top-selling', TopSellingView, basename='top-selling')
router.register('sale-by-shop', SaleByShopView, basename='sale-by-shop')
router.register('purchase-summary', PurchaseView, basename='purchase-summary')
router.register('inventory-csv', InventoryCSVLoaderView, basename='inventory-csv')

urlpatterns = [
    path('', include(router.urls))
]
