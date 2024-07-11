import logging
from collections import OrderedDict

import rest_framework.viewsets
from django.db.models import Count
from rest_framework import serializers
from rest_framework.response import Response

from .filters import DxFilterBackend
from .pagination import TakeSkipPagination
from .summary import SummaryMixin


def format_items(lvl_dict, lvl_items):
    if lvl_dict is None:
        return
    for key in lvl_dict:
        key_dict = lvl_dict[key]
        item = {"key": key}
        lvl_items.append(item)

        if "count" in key_dict:
            item["count"] = key_dict["count"]
        if "summary" in key_dict:
            item["summary"] = key_dict["summary"]

        if key_dict["items"] is None:
            item["items"] = None
        else:
            item["items"] = []
            format_items(key_dict["items"], item["items"])


class DxListModelMixin(rest_framework.mixins.ListModelMixin, SummaryMixin):
    pagination_class = TakeSkipPagination
    filter_backends = [
        DxFilterBackend,
        *rest_framework.viewsets.ModelViewSet.filter_backends,
    ]

    @staticmethod
    def get_field_type(field):
        if (
            isinstance(field, (serializers.Serializer, serializers.JSONField))
            or hasattr(field, "many")
            and field.many
        ):
            return "object"
        elif isinstance(
            field,
            (
                serializers.IntegerField,
                serializers.DecimalField,
                serializers.FloatField,
            ),
        ):
            return "number"
        elif isinstance(field, (serializers.DateField, serializers.DateTimeField)):
            return "date"
        return "string"

    def _field_type_list(self):
        """
        Get field types from serializer class
        :return: Dict {field_name: field_type as string}
                Types: 'object', 'number', 'date', 'string'
        """
        result = {}
        try:
            fields = self.get_serializer().fields
            for field_name, field in fields.items():
                result[field_name] = self.get_field_type(field)
        except Exception as e:
            logging.exception(e)
        finally:
            return Response(result)

    def list(self, request, *args, **kwargs):
        list_type = self.request.query_params.get("list_types", "False").lower()
        if list_type == "true":
            return self._field_type_list()

        queryset = self.filter_queryset(self.get_queryset())
        group = self.get_param_from_request(request, "group")
        if group:
            return self._grouped_list(group, queryset, request)
        else:
            return self._not_grouped_list(queryset, request)

    def _grouped_list(self, groups, queryset, request):
        require_group_count = self.get_param_from_request(request, "requireGroupCount")
        require_total_count = self.get_param_from_request(request, "requireTotalCount")

        if not isinstance(groups, list):
            groups = [groups]

        group_field_names = {self.get_group_field_name(group) for group in groups}
        ordering = self.get_ordering(self.get_serializer(), groups)
        group_queryset = (
            queryset.values(*group_field_names)
            .annotate(count=Count("pk"))
            .order_by(*ordering)
            .distinct()
        )
        group_summary = self.get_param_from_request(request, "groupSummary")
        if group_summary:
            if not isinstance(group_summary, list):
                group_summary = [group_summary]
            group_queryset = self.add_summary_annotate(group_queryset, group_summary)

        page = self.paginate_queryset(group_queryset)
        res_dict = {}
        if require_group_count:
            res_dict["groupCount"] = group_queryset.count()
        if require_total_count:
            res_dict["totalCount"] = queryset.count()

        result = page if page else group_queryset
        data_dict = {}
        for row in result:
            lvl_dict = data_dict
            for group in groups:
                group_field_name = self.get_group_field_name(group)
                key = row[group_field_name]

                if key in lvl_dict:
                    key_dict = lvl_dict[key]
                else:
                    key_dict = {}
                    lvl_dict[key] = key_dict

                if group["isExpanded"]:
                    if "items" not in key_dict:
                        key_dict["items"] = {}
                    lvl_dict = key_dict["items"]
                else:
                    key_dict["items"] = None
                    key_dict["count"] = row["count"]

                    summary_pairs = list(
                        filter(lambda x: x[0].startswith("gs__"), row.items())
                    )
                    if summary_pairs:
                        summary_pairs.sort(key=lambda x: x[0])
                        summary = [x[1] for x in summary_pairs]
                        key_dict["summary"] = summary

        res_dict["data"] = []
        format_items(data_dict, res_dict["data"])

        return Response(res_dict)

    def _not_grouped_list(self, queryset, request):
        res_dict = OrderedDict()
        page = self.paginate_queryset(queryset)
        if page is None:
            serializer = self.get_serializer(queryset, many=True)
        else:
            serializer = self.get_serializer(page, many=True)
            res_dict["totalCount"] = self.paginator.count
        total_summary = self.get_param_from_request(request, "totalSummary")
        if total_summary is not None and total_summary:
            if not isinstance(total_summary, list):
                total_summary = [total_summary]
            res_dict["summary"] = self.calc_total_summary(queryset, total_summary)
        res_dict["data"] = serializer.data
        return Response(res_dict)

    def get_group_field_name(self, group: dict):
        field_name = self.get_field_name_from_source(
            self.get_serializer(), group["selector"]
        )
        if "groupInterval" in group:
            field_name += "__" + group["groupInterval"]
        return field_name


class DxReadOnlyModelViewSet(
    rest_framework.mixins.RetrieveModelMixin,
    DxListModelMixin,
    rest_framework.viewsets.GenericViewSet,
):
    """
    A viewset that provides default `list()` and `retrieve()` actions.
    That support DX Extreme Datagrid filters and actions
    """

    pass


class DxModelViewSet(
    rest_framework.mixins.CreateModelMixin,
    rest_framework.mixins.RetrieveModelMixin,
    rest_framework.mixins.UpdateModelMixin,
    rest_framework.mixins.DestroyModelMixin,
    DxListModelMixin,
    rest_framework.viewsets.GenericViewSet,
):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    That support DX Extreme Datagrid filters and actions
    """

    pass
