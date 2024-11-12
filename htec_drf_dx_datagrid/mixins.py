import json

from rest_framework import serializers


class DxMixin(object):
    FILTER = "filter"
    SORT = "sort"
    GROUP_SUMMARY = "groupSummary"
    TOTAL_SUMMARY = "totalSummary"
    GROUP = "group"
    DX_PARAMS = [FILTER, SORT, GROUP_SUMMARY, TOTAL_SUMMARY, GROUP]

    @staticmethod
    def get_param_from_request(request, param_name):
        def json_loads(value, default):
            try:
                json_object = json.loads(value)
            except json.JSONDecodeError:
                return default
            return json_object

        param_list = []
        # Read from GET because sometimes you could be need modify something in query_params
        if param_name in request.GET:
            param_list = request.GET.getlist(param_name)
        elif param_name + "[]" in request.GET:
            param_list = request.GET.getlist(param_name + "[]")

        param_list = [json_loads(x, x) for x in param_list]
        if len(param_list) == 1:
            return param_list[0]
        elif len(param_list) > 1:
            return param_list

        return request.data.get(param_name)

    def get_ordering(self, serializer, dx_sort_list):
        result = []
        if dx_sort_list is None:
            return result
        if isinstance(dx_sort_list, dict):
            dx_sort_list = [dx_sort_list]
        for param in dx_sort_list:
            field_name = self.get_field_name_from_source(serializer, param["selector"])
            desc = "-" if "desc" in param and param["desc"] else ""
            result.append(desc + field_name)
        return result

    def get_field_name_from_source(self, serializer, field):
        """
        Get the field name needed in query from source of serializer
        """
        if type(field) is str:
            field = serializer.fields.get(field)
        f_name = field.field_name
        if serializer:
            if isinstance(field, serializers.SerializerMethodField):  # SBG > Probar
                source = getattr(field, "_kwargs", {}).get("source", None)
                if source:
                    f_name = source.replace(" ", "").split(",")
                    f_name = f_name.pop() if len(f_name) == 1 else f_name
            elif hasattr(field, "source"):
                f_name = field.source
        return f_name.replace(".", "__")
