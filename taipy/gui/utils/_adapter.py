from __future__ import annotations

import typing as t
import warnings

from ..icon import Icon
from . import _MapDict


class _Adapter:
    def __init__(self):
        self.__adapter_for_type: t.Dict[str, t.Callable] = {}
        self.__type_for_variable: t.Dict[str, str] = {}

    def _add_for_type(self, type_name: str, adapter: t.Callable) -> None:
        self.__adapter_for_type[type_name] = adapter

    def _add_type_for_var(self, var_name: str, type_name: str) -> None:
        self.__type_for_variable[var_name] = type_name

    def _get_for_type(self, type_name: str) -> t.Optional[t.Callable]:
        return self.__adapter_for_type.get(type_name)

    def _run_for_var(self, var_name: str, value: t.Any, id_only=False) -> t.Any:
        adapter = self.__get_for_var(var_name, value)
        if adapter:
            ret = self._run(adapter, value, var_name, id_only)
            if ret is not None:
                return ret
        return value

    def __get_for_var(self, var_name: str, value: t.Any) -> t.Optional[t.Callable]:
        adapter = None
        type_name = self.__type_for_variable.get(var_name)
        if not isinstance(type_name, str):
            adapter = self.__adapter_for_type.get(var_name)
            type_name = var_name if callable(adapter) else type(value).__name__
        if adapter is None:
            adapter = self.__adapter_for_type.get(type_name)
        if callable(adapter):
            return adapter
        return None

    def _get_elt_per_ids(self, var_name: str, lov: t.List[t.Any]) -> t.Dict[str, t.Any]:
        dict_res = {}
        adapter = self.__get_for_var(var_name, lov[0] if lov else None)
        for idx, value in enumerate(lov):
            try:
                result = adapter(value if not isinstance(value, _MapDict) else value._dict) if adapter else value
                dict_res[self.__get_id(result)] = value
                children = self.__get_children(result)
                if children is not None:
                    dict_res.update(self._get_elt_per_ids(var_name, children))
            except Exception as e:
                warnings.warn(f"Can't run adapter for {var_name}: {e}")
        return dict_res

    def _run(
        self, adapter: t.Callable, value: t.Any, var_name: str, id_only=False
    ) -> t.Union[t.Tuple[str, ...], str, None]:
        if value is None:
            return None
        try:
            result = adapter(value if not isinstance(value, _MapDict) else value._dict)
            result = self._get_valid_result(result, id_only)
            if result is None:
                warnings.warn(
                    f"Adapter for {var_name} did not return a valid result. Please check the documentation on List of Values Adapters."
                )
            else:
                if not id_only and len(result) > 2 and isinstance(result[2], list) and len(result[2]) > 0:
                    result = (result[0], result[1], self.__on_tree(adapter, result[2]))
                return result
        except Exception as e:
            warnings.warn(f"Can't run adapter for {var_name}: {e}")
        return None

    def __on_tree(self, adapter: t.Callable, tree: t.List[t.Any]):
        ret_list = []
        for idx, elt in enumerate(tree):
            ret = self._run(adapter, elt, adapter.__name__)
            if ret is not None:
                ret_list.append(ret)
        return ret_list

    def _get_valid_result(
        self, value: t.Any, id_only=False
    ) -> t.Union[t.Tuple[str, ...], str, None]:
        id = self.__get_id(value)
        if id_only:
            return id
        label = self.__get_label(value)
        if label is None:
            return None
        children = self.__get_children(value)
        return (id, label) if children is None else (id, label, children)  # type: ignore

    def __get_id(self, value: t.Any) -> str:
        if isinstance(value, str):
            return value
        elif isinstance(value, (list, tuple)) and len(value):
            return self.__get_id(value[0])
        elif hasattr(value, "id"):
            return str(value.id)
        elif hasattr(value, "__getitem__") and "id" in value:
            return str(value.get("id"))
        else:
            return str(value)

    def __get_label(self, value: t.Any) -> t.Union[str, t.Dict, None]:
        if isinstance(value, (str, Icon)):
            return Icon.get_dict_or(value)
        elif isinstance(value, (list, tuple)) and len(value) > 1:
            return self.__get_label(value[1])
        elif hasattr(value, "label"):
            return Icon.get_dict_or(value.label)
        elif hasattr(value, "__getitem__") and "label" in value:
            return Icon.get_dict_or(value["label"])
        return None

    def __get_children(self, value: t.Any) -> t.Union[t.List[t.Any], None]:
        if isinstance(value, (tuple, list)) and len(value) > 2:
            return value[2] if isinstance(value[2], list) else [value[2]]
        elif hasattr(value, "children"):
            return value.children if isinstance(value.children, list) else [value.children]
        elif hasattr(value, "__getitem__") and "children" in value:
            return value["children"] if isinstance(value["children"], list) else [value["children"]]
        return None
