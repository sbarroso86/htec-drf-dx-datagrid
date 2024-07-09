import ast

from django.db.models import Q
from rest_framework import filters, fields

from .exceptions import HtecDrfDxDatagridException
from .mixins import DxMixin


class DxFilterBackend(filters.BaseFilterBackend, DxMixin):

    def __init__(self):
        self.is_case_sensitive = self.get_case_sensitive()
        self.serializer = None

    @staticmethod
    def is_node(dx_filter: list):
        """
        Dev extreme datagrid the filter node is [field_name, operator, value]
        :param dx_filter: List with dev extreme datagrid filter
        :return: True when dx_filter is a node
        """
        for elem in dx_filter:
            if isinstance(elem, list):
                return False
        return True

    def _to_django_operator(self, operator: str, value, is_char_field):
        if operator == "notcontains":
            return "__contains" if self.is_case_sensitive else "__icontains"
        if operator == "<>":
            return ""
        if operator == "=":
            if isinstance(value, str) and is_char_field:
                return "__exact" if self.is_case_sensitive else "__iexact"
            return ""
        if operator == ">":
            return "__gt"
        if operator == "<":
            return "__lt"
        if operator == ">=":
            return "__gte"
        if operator == "<=":
            return "__lte"
        return "__" + operator if self.is_case_sensitive else "__i" + operator

    @staticmethod
    def _check_value(value):
        """
        Check value is correct format for queryset
        FYI: In number fields django support filter doesn't matter if it is string
        or number, but when it is a list we need parse string to list
        :param value: value from request
        :return: value to queryset
        """
        try:
            if type(value) is str:
                aux_value = ast.literal_eval(value)
                if type(aux_value) is list:
                    return aux_value
        except (ValueError, SyntaxError):
            pass
        return value

    def is_char_field(self, field_name):
        field = self.serializer.fields.get(field_name)
        return isinstance(field, fields.CharField)

    def __node_to_q(self, node: list):
        """
        Generate Query for Node filter
        :param node: Node with dev extreme datagrid filter
                    [field_name, operator, value]
        :return: Query
        """
        field_name = self.get_field_name_from_source(self.serializer, node[0])
        is_char_field = self.is_char_field(node[0])
        value = self._check_value(node[2])
        is_negative = node[1] == "<>" or node[1] == "notcontains"
        operator = self._to_django_operator(node[1], value, is_char_field)

        q_expr = Q(**{field_name + operator: value})

        return ~q_expr if is_negative else q_expr

    def __generate_q_expr(self, dx_filter):
        if dx_filter is None or not dx_filter:
            return None
        if self._is_node(dx_filter):
            return self.__node_to_q(dx_filter)
        else:
            q_elems = []

            for elem in dx_filter:
                if isinstance(elem, list):
                    q_elems.append(self.__generate_q_expr(elem))
                elif elem in ["and", "or", "!"]:
                    q_elems.append(elem)
                else:
                    raise HtecDrfDxDatagridException("Could not implement this search")
            if q_elems[0] == "!":
                q_expr = ~q_elems[1]
            else:
                q_expr = q_elems[0]
                for num_pair in range(0, len(q_elems) // 2):
                    oper = q_elems[num_pair * 2 + 1]
                    if oper == "and":
                        q_expr = q_expr & q_elems[(num_pair + 1) * 2]
                    else:
                        q_expr = q_expr | q_elems[(num_pair + 1) * 2]
            return q_expr

    def filter_queryset(self, request, queryset, view):
        self.serializer = view.get_serializer()
        res_queryset = queryset
        dx_filter = self.get_param_from_request(request, "filter")
        if dx_filter:
            q_expr = self.__generate_q_expr(dx_filter)
            if q_expr is not None:
                res_queryset = res_queryset.filter(q_expr)
        sort = self.get_param_from_request(request, "sort")
        if sort:
            ordering = self.get_ordering(sort)
            if ordering:
                res_queryset = res_queryset.order_by(*ordering)
        return res_queryset

    def get_case_sensitive(self):
        from django.conf import settings

        try:
            return settings.REST_FRAMEWORK["DRF_DX_DATAGRID"]["FILTER_CASE_SENSITIVE"]
        except (AttributeError, KeyError):
            return True
