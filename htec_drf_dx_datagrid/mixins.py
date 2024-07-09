import json

from rest_framework import serializers


class DxMixin(object):

    @staticmethod
    def get_param_from_request(request, param_name):
        def json_loads(value, default):
            try:
                json_object = json.loads(value)
            except json.JSONDecodeError:
                return default
            return json_object

        param_list = []
        if param_name in request.query_params:
            param_list = request.query_params.getlist(param_name)
        elif param_name + "[]" in request.query_params:
            param_list = request.query_params.getlist(param_name + "[]")

        param_list = [json_loads(x, x) for x in param_list]
        if len(param_list) == 1:
            return param_list[0]
        elif len(param_list) > 1:
            return param_list

        return request.data.get(param_name)

    @classmethod
    def get_ordering(cls, serializer, dx_sort_list):
        result = []
        if dx_sort_list is None:
            return result
        if isinstance(dx_sort_list, dict):
            dx_sort_list = [dx_sort_list]
        for param in dx_sort_list:
            field_name = cls.get_field_name_from_source(serializer, param["selector"])
            desc = "-" if "desc" in param and param["desc"] else ""
            result.append(desc + field_name)
        return result

    @staticmethod
    def get_field_name_from_source(serializer, f_name):
        """
        Get the field name needed in query from source of serializer
        """
        if serializer:
            field = serializer.fields.get(f_name)
            if isinstance(field, serializers.SerializerMethodField):  # SBG > Probar
                source = getattr(field, "_kwargs", {}).get("source", None)
                if source:
                    f_name = source.replace(" ", "").split(",")
                    f_name = f_name.pop() if len(f_name) == 1 else f_name
            elif hasattr(field, "source"):
                f_name = field.source
        return f_name.replace(".", "__")
