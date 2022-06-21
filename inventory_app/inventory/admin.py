from django.contrib import admin

from .models import Inventory, InventoryGroup, Shop,  Invoice,  InvoiceItem


admin.site.register(InventoryGroup)
admin.site.register(Inventory)
admin.site.register(Shop)
admin.site.register(Invoice)
admin.site.register(InvoiceItem)
