from django.db import models

from my_user.models import CustomUser
from my_user.utils import add_user_activities


class InventoryGroup(models.Model):
    """ Модель групп инвентаря """

    created_by = models.ForeignKey(
        CustomUser, null=True, related_name='inventory_groups', on_delete=models.SET_NULL
    )
    name = models.CharField(max_length=100, unique=True)
    belongs_to = models.ForeignKey(
        'self', blank=True, null=True, related_name='group_relations', on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Inventory Group'
        verbose_name_plural = 'Inventory Groups'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_name = self.name

    def save(self, *args, **kwargs):
        action = f'added new group - "{self.name}"'
        if self.pk is not None:
            action = f'updated group from - "{self.old_name}" to "{self.name}"'
        super().save(*args, **kwargs)
        add_user_activities(self.created_by, action=action)

    def delete(self, *args, **kwargs):
        created_by = self.created_by
        action = f'deleted group - "{self.name}"'
        super().delete(*args, **kwargs)
        add_user_activities(created_by, action=action)

    def __str__(self):
        return self.name


class Inventory(models.Model):
    """ Модель инвентаря """

    created_by = models.ForeignKey(
        CustomUser, null=True, related_name='inventory_items', on_delete=models.SET_NULL
    )
    code = models.CharField(max_length=10, unique=True, null=True)
    image = models.ImageField(upload_to='inventory_image/%Y/%m/%d/', blank=True, null=True)
    group = models.ForeignKey(
        InventoryGroup, related_name='inventories', null=True, on_delete=models.SET_NULL
    )
    total = models.PositiveIntegerField(default=0)
    remaining = models.PositiveIntegerField(null=True)
    name = models.CharField(max_length=255)
    price = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Inventory'
        verbose_name_plural = 'Inventories'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            self.remaining = self.total

        super().save(*args, **kwargs)

        if is_new:
            id_length = len(str(self.id))
            code_length = 6 - id_length
            zeros = ''.join('0' for i in range(code_length))
            self.code = f'{zeros}{self.id}'
            self.save()
        action = f'added new inventory item "{self.name}" with code "{self.code}"'

        if not is_new:
            action = f'updated inventory item "{self.name}" with code "{self.code}"'
        add_user_activities(self.created_by, action=action)

    def delete(self, *args, **kwargs):
        created_by = self.created_by
        action = f'deleted inventory item "{self.name}" with code "{self.code}"'
        super().delete(*args, **kwargs)
        add_user_activities(created_by, action=action)

    def __str__(self):
        return f'{self.name} - {self.code}'


class Shop(models.Model):
    """ Модель магазинов """

    created_by = models.ForeignKey(
        CustomUser, null=True, related_name='shops', on_delete=models.SET_NULL
    )
    name = models.CharField(max_length=75, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Shop'
        verbose_name_plural = 'Shops'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_name = self.name

    def save(self, *args, **kwargs):
        action = f'added new shop - "{self.name}"'
        if self.pk is not None:
            action = f'updated shop from - "{self.old_name}" to "{self.name}"'
        super().save(*args, **kwargs)
        add_user_activities(self.created_by, action=action)

    def delete(self, *args, **kwargs):
        created_by = self.created_by
        action = f'deleted shop - "{self.name}"'
        super().delete(*args, **kwargs)
        add_user_activities(created_by, action=action)

    def __str__(self):
        return self.name


class Invoice(models.Model):
    """ Модель счета """

    created_by = models.ForeignKey(
        CustomUser, null=True, related_name='invoices', on_delete=models.SET_NULL
    )
    shop = models.ForeignKey(Shop, related_name='sale_shop', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'

    def save(self, *args, **kwargs):
        action = f'added new invoice'
        super().save(*args, **kwargs)
        add_user_activities(self.created_by, action=action)

    def delete(self, *args, **kwargs):
        created_by = self.created_by
        action = f'deleted invoice - "{self.id}"'
        super().delete(*args, **kwargs)
        add_user_activities(created_by, action=action)

    def __str__(self):
        return f'{self.id} - {self.shop} - {self.created_at}'


class InvoiceItem(models.Model):
    """ Модель инвентаря из счета """

    invoice = models.ForeignKey(Invoice, related_name='invoice_items', on_delete=models.CASCADE)
    item = models.ForeignKey(
        Inventory, related_name='inventory_invoices', null=True, on_delete=models.SET_NULL
    )
    item_name = models.CharField(max_length=255, null=True)
    item_code = models.CharField(max_length=20, null=True)
    quantity = models.PositiveIntegerField(default=1)
    amount = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Invoice Item'
        verbose_name_plural = 'Invoice Items'

    def save(self, *args, **kwargs):
        if self.item.remaining < self.quantity:
            raise Exception(f'Item with code {self.item.code} does not have enough quantity!')

        self.item_name = self.item.name
        self.item_code = self.item.code

        self.amount = self.quantity * self.item.price
        self.item.remaining = self.item.remaining - self.quantity
        self.item.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.item_code} - {self.item_name} - {self.quantity} - {self.invoice.shop.name}'
