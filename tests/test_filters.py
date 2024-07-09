import pytest
from mock.mock import patch
from htec_drf_dx_datagrid.filters import DxFilterBackend


class TestDxFilterBackend:

    DATA_TEST_TO_DJANGO_OPERATOR = (
        # is_case_sensitive, operator, value, is_char_field, expected
        [True, "notcontains", None, None, "__contains"],
        [False, "notcontains", None, None, "__icontains"],
        [None, "<>", None, None, ""],
        [True, "=", "value", True, "__exact"],
        [False, "=", "value", True, "__iexact"],
        [None, "=", 2024, True, ""],
        [None, "=", "2024-01-01", False, ""],
        [None, ">", None, None, "__gt"],
        [None, "<", None, None, "__lt"],
        [None, ">=", None, None, "__gte"],
        [None, "<=", None, None, "__lte"],
        [True, "contains", None, None, "__contains"],
        [False, "contains", None, None, "__icontains"],
    )

    @pytest.mark.parametrize(
        "is_case_sensitive, operator, value, is_char_field, expected",
        DATA_TEST_TO_DJANGO_OPERATOR,
    )
    @patch("htec_drf_dx_datagrid.filters.DxFilterBackend.get_case_sensitive")
    def test_to_django_operator(
        self,
        m_get_case_sensitive,
        is_case_sensitive,
        operator,
        value,
        is_char_field,
        expected,
    ):
        m_get_case_sensitive.return_value = is_case_sensitive
        result = DxFilterBackend()._to_django_operator(operator, value, is_char_field)
        assert result == expected

    DATA_TEST_CHECK_VALUE = (
        # value, expeted
        [2, 2],
        ["value", "value"],
        ["['lista']", ["lista"]],
    )

    @pytest.mark.parametrize("value, expeted", DATA_TEST_CHECK_VALUE)
    def test_check_value(self, value, expeted):
        result = DxFilterBackend._check_value(value)
        assert result == expeted
