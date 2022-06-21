import codecs
import csv

from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.db.models import Count, Sum, F
from django.db.models.functions import Coalesce, TruncMonth

from .serializers import (
    InventorySerializer, InventoryGroupSerializer, ShopSerializer, InvoiceSerializer,
    InventoryWithSumSerializer, ShopWithAmountSerializer
)
from .models import Inventory, Shop, Invoice, InvoiceItem, InventoryGroup
from .utils import CustomPagination, get_query
from my_user.permissions import IsAuthenticatedCustom
from my_user.models import CustomUser


class InventoryView(ModelViewSet):
    """ Представление для получения информации об инвентаре """

    queryset = Inventory.objects.select_related('group', 'created_by')
    serializer_class = InventorySerializer
    permission_classes = (IsAuthenticatedCustom,)
    pagination_class = CustomPagination

    def get_queryset(self):
        if self.request.method.lower() != 'get':
            return self.queryset

        data = self.request.query_params.dict()
        data.pop('page', None)
        keyword = data.pop('keyword', None)

        results = self.queryset.filter(**data)

        if keyword:
            search_fields = (
                'code', 'created_by__fullname', 'created_by__email', 'group__name', 'name'
            )
            query = get_query(keyword, search_fields)
            return results.filter(query)
        return results

    def create(self, request, *args, **kwargs):
        request.data.update({'created_by_id': request.user.id})
        return super().create(request, *args, **kwargs)


class InventoryGroupView(ModelViewSet):
    """ Представление для получения информации о группах инвентаря, сколько в них товаров """

    queryset = InventoryGroup.objects.select_related(
        'belongs_to', 'created_by'
    ).prefetch_related('inventories')
    serializer_class = InventoryGroupSerializer
    permission_classes = (IsAuthenticatedCustom,)
    pagination_class = CustomPagination

    def get_queryset(self):
        if self.request.method.lower() != 'get':
            return self.queryset

        data = self.request.query_params.dict()
        data.pop('page', None)
        keyword = data.pop('keyword', None)

        results = self.queryset.filter(**data)

        if keyword:
            search_fields = (
                'created_by__fullname', 'created_by__email', 'name'
            )
            query = get_query(keyword, search_fields)
            results = results.filter(query)

        return results.annotate(
            total_items=Count('inventories')
        )

    def create(self, request, *args, **kwargs):
        request.data.update({'created_by_id': request.user.id})
        return super().create(request, *args, **kwargs)


class ShopView(ModelViewSet):
    """ Представление для получения информации про магазины """

    queryset = Shop.objects.select_related('created_by')
    serializer_class = ShopSerializer
    permission_classes = (IsAuthenticatedCustom,)
    pagination_class = CustomPagination

    def get_queryset(self):
        if self.request.method.lower() != 'get':
            return self.queryset

        data = self.request.query_params.dict()
        data.pop('page', None)
        keyword = data.pop('keyword', None)

        results = self.queryset.filter(**data)

        if keyword:
            search_fields = (
                'created_by__fullname', 'created_by__email', 'name'
            )
            query = get_query(keyword, search_fields)
            results = results.filter(query)

        return results

    def create(self, request, *args, **kwargs):
        request.data.update({'created_by_id': request.user.id})
        return super().create(request, *args, **kwargs)


class InvoiceView(ModelViewSet):
    """ Представление для получения информации о счетах """

    queryset = Invoice.objects.select_related(
        'created_by', 'shop'
    ).prefetch_related('invoice_items')
    serializer_class = InvoiceSerializer
    permission_classes = (IsAuthenticatedCustom,)
    pagination_class = CustomPagination

    def get_queryset(self):
        if self.request.method.lower() != 'get':
            return self.queryset

        data = self.request.query_params.dict()
        data.pop('page', None)
        keyword = data.pop('keyword', None)

        results = self.queryset.filter(**data)

        if keyword:
            search_fields = (
                'created_by__fullname', 'created_by__email', 'shop__name'
            )
            query = get_query(keyword, search_fields)
            results = results.filter(query)

        return results

    def create(self, request, *args, **kwargs):
        request.data.update({'created_by_id': request.user.id})
        return super().create(request, *args, **kwargs)


class SummaryView(ModelViewSet):
    """ Представление для получения количества инвентаря, групп, магазинов, пользователей """

    http_method_names = ('get',)
    queryset = InventoryView.queryset
    permission_classes = (IsAuthenticatedCustom,)

    def list(self, *args, **kwargs):
        total_inventory = InventoryView.queryset.filter(
            remaining__gt=0
        ).count()
        total_group = InventoryGroupView.queryset.count()
        total_shop = ShopView.queryset.count()
        total_users = CustomUser.objects.filter(is_superuser=False).count()

        return Response({
            'total_inventory': total_inventory,
            'total_group': total_group,
            'total_shop': total_shop,
            'total_users': total_users
        })


class TopSellingView(ModelViewSet):
    """ Представление для получения информации про 10 штук самого продаваемого инвентаря """

    http_method_names = ('get',)
    queryset = InventoryView.queryset
    permission_classes = (IsAuthenticatedCustom,)

    def list(self, request, *args, **kwargs):
        query_data = request.query_params.dict()
        total = query_data.get('total', None)
        query = self.queryset

        if not total:
            start_date = query_data.get('start_date', None)
            end_date = query_data.get('end_date', None)

            if start_date:
                query = query.filter(
                    inventory_invoices__created_at__range=[start_date, end_date]
                )

        items = query.annotate(
            sum_of_item=Coalesce(
                Sum('inventory_invoices__quantity'), 0
            )
        ).order_by('-sum_of_item')[0:10]
        return Response(InventoryWithSumSerializer(items, many=True).data)


class SaleByShopView(ModelViewSet):
    """ Представление для получения информации про продажи """

    http_method_names = ('get',)
    queryset = InventoryView.queryset
    permission_classes = (IsAuthenticatedCustom,)

    def list(self, request, *args, **kwargs):
        query_data = request.query_params.dict()
        total = query_data.get('total', None)
        monthly = query_data.get('monthly', None)
        query = ShopView.queryset

        if not total:
            start_date = query_data.get('start_date', None)
            end_date = query_data.get('end_date', None)

            if start_date:
                query = query.filter(
                    sale_shop__created_at__range=[start_date, end_date]
                )

        if monthly:
            shops = query.annotate(month=TruncMonth('created_at')).values(
                'month', 'name').annotate(amount_total=Sum(
                    F('sale_shop__invoice_items__quantity') * F('sale_shop__invoice_items__amount')
                ))
        else:
            shops = query.annotate(amount_total=Sum(
                    F('sale_shop__invoice_items__quantity') * F('sale_shop__invoice_items__amount')
                )).order_by('-amount_total')

        return Response(ShopWithAmountSerializer(shops, many=True).data)


class PurchaseView(ModelViewSet):
    """ Представление для получения информации про количество заказов и общую сумму покупок """

    http_method_names = ('get',)
    queryset = InvoiceView.queryset
    permission_classes = (IsAuthenticatedCustom,)

    def list(self, request, *args, **kwargs):
        query_data = request.query_params.dict()
        total = query_data.get('total', None)
        query = InvoiceItem.objects.select_related("invoice", "item")

        if not total:
            start_date = query_data.get("start_date", None)
            end_date = query_data.get("end_date", None)

            if start_date:
                query = query.filter(
                    created_at__range=[start_date, end_date]
                )

        query = query.aggregate(
            amount_total=Sum(F('amount') * F('quantity')), total=Sum('quantity')
            )

        return Response({
            "price": "0.00" if not query.get("amount_total") else query.get("amount_total"),
            "count": 0 if not query.get("total") else query.get("total"),
        })


class InventoryCSVLoaderView(ModelViewSet):
    """ Представление для добавления инвентаря их CSV файлов """

    http_method_names = ('post',)
    queryset = InventoryView.queryset
    permission_classes = (IsAuthenticatedCustom,)
    serializer_class = InventorySerializer

    def create(self, request, *args, **kwargs):
        try:
            data = request.FILES['data']
        except Exception as e:
            raise Exception("You need to provide inventory CSV 'data'")

        inventory_items = []

        try:
            csv_reader = csv.reader(codecs.iterdecode(data, 'utf-8'))
            for row in csv_reader:
                if not row[0]:
                    continue
                inventory_items.append(
                    {
                        "group_id": row[0],
                        "total": row[1],
                        "name": row[2],
                        "price": row[3],
                        "created_by_id": request.user.id
                    }
                )
        except csv.Error as e:
            raise Exception(e)

        if not inventory_items:
            raise Exception("CSV file cannot be empty")

        data_validation = self.serializer_class(data=inventory_items, many=True)
        data_validation.is_valid(raise_exception=True)
        data_validation.save()

        return Response({"success": "Inventory items added successfully"})
