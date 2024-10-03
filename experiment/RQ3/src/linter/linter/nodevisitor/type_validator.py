from src.linter.linter.nodevisitor.result import Success, Failure, Result

from typing import get_origin, get_args, Literal, Union, Optional, TypedDict, NotRequired, Generic, TypeVar
import pydantic
import pydantic_core
import json
T = TypeVar("T", covariant=True)


class TypeValidator(Generic[T]):
    """
    Validates an object against a given Python type.
    """

    _adapted_type: pydantic.TypeAdapter[T]

    def __init__(self, py_type: type[T]):
        """
        Args:

            py_type: The schema type to validate against.
        """
        super().__init__()
        self._adapted_type = pydantic.TypeAdapter(py_type)

    def validate(self, obj: object) -> Result[T]:
        """
        :param obj is 'object' type, not 'str' type anymore

        Validates the given Python object according to the associated schema type.

        Returns a `Success[T]` object containing the object if validation was successful.
        Otherwise, returns a `Failure` object with a `message` property describing the error.
        """
        try:
            json_str = pydantic_core.to_json(obj)
            typed_dict = self._adapted_type.validate_json(json_str, strict=True)
            return Success(typed_dict)
        except pydantic.ValidationError as validation_error:
            return _handle_error(validation_error)


def _handle_error(validation_error: pydantic.ValidationError) -> Failure:
    error_strings: list[str] = []
    for error in validation_error.errors(include_url=False):
        error_string = ""
        loc_path = error["loc"]
        if loc_path:
            error_string += f"In path `{'.'.join(map(str, loc_path))}` "
        else:
            error_string += "In Root "
        input = error["input"]
        error_string += f"has '{error['type']}' error for value `{json.dumps(input)}` because: {error['msg']}"
        error_strings.append(error_string)

    if len(error_strings) > 1:
        failure_message = "has several possible issues may have occurred:\n"
        error_count = 1
        for error_string in error_strings:
            failure_message += f"({error_count}){error_string}\n"
            error_count += 1
    else:
        failure_message = ""
        failure_message += "\n".join(error_strings)

    return Failure(failure_message)


def create_instance(typ):
    origin = get_origin(typ)
    args = get_args(typ)

    if origin is Literal:
        return args[0]

    elif origin is Union and type(None) in args:
        non_none_type = next(t for t in args if t is not type(None))
        return create_instance(non_none_type)

    elif origin is NotRequired:
        return create_instance(args[0])

    # 基本类型处理
    elif typ is str:
        return " "
    elif typ is int:
        return 0
    elif typ is float:
        return 0.0
    elif typ is bool:
        return False

    # 处理 list 类型
    elif origin is list or typ is list:
        if args:
            return [create_instance(args[0])]
        else:
            return []

    # 处理 dict 类型
    elif origin is dict or typ is dict:
        if args and len(args) == 2:
            return {create_instance(args[0]): create_instance(args[1])}
        else:
            return {}

    # 处理 TypedDict 类型
    elif isinstance(typ, type) and issubclass(typ, dict) and hasattr(typ, '__annotations__'):
        instance = {}
        for key, value_type in typ.__annotations__.items():
            instance[key] = create_instance(value_type)
        return instance
    elif typ is type(None):
        return None

    return None


def get_types_from_string(typeinfo_str):
    namespace = {}
    import_statements = """
from typing import Any, Optional, Union, Tuple, List, Dict, Set, FrozenSet, Literal, TypedDict
"""
    exec(import_statements, namespace)
    exec(typeinfo_str, namespace)
    return namespace
