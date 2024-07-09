# coding: utf-8
from django.db.models import Count, Avg, Max, Min, Sum, QuerySet
from rest_framework.exceptions import ValidationError

from htec_drf_dx_datagrid.mixins import DxMixin


class SummaryMixin(DxMixin):

    @staticmethod
    def get_aggregate_function(function_name: str, field_name: str):
        if function_name == "count":
            return Count(field_name)
        elif function_name == "avg":
            return Avg(field_name)
        elif function_name == "max":
            return Max(field_name)
        elif function_name == "min":
            return Min(field_name)
        elif function_name == "sum":
            return Sum(field_name)
        else:
            raise ValidationError(detail=f"Unsupported summary type '{function_name}'")

    def calc_total_summary(self, queryset: QuerySet, summary_list: list):
        result = []
        for summary in summary_list:
            field_name = self.get_field_name_from_source(
                self.get_serializer(), summary["selector"]
            )
            aggr_function = self.get_aggregate_function(
                summary["summaryType"], field_name
            )
            if aggr_function is None:
                result.append(None)
            else:
                summary_qset = queryset.aggregate(aggr_function)
                result.append(list(summary_qset.values())[0])
        return result

    def add_summary_annotate(self, queryset, summary_list):
        summary_param_dict = {}
        for summary in summary_list:
            field_name = self.get_field_name_from_source(
                self.get_serializer(), summary["selector"]
            )
            aggr_function = self.get_aggregate_function(
                summary["summaryType"], field_name
            )
            param_name = "gs__" + str(summary_list.index(summary))
            summary_param_dict[param_name] = aggr_function
        return queryset.annotate(**summary_param_dict)
