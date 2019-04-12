import inspect
import types
import typing
from collections.abc import Container, Mapping

class Validator:

    def is_valid(self, value):
        try:
            self(value)
        except (TypeError, ValueError):
            return False
        return True


class SimpleValidator(Validator):
    def __init__(self, _type):
        self._type = _type

    def __call__(self, value):
        if not isinstance(value, self._type):
            raise TypeError(f"Vaue {value !r} is not of type '{self._type.__name__}'.")


class ContainerValidator(Validator):
    def __init__(self, _type):
        self.base = _type.__origin__
        self.inner_type = validator_for(_type.__args__[0])

    def __call__(self, value):
        if not isinstance(value, self.base):
            raise TypeError(f"{value !r} is not a Container")
        self.validate_contents(value)

    def validate_contents(self, value):
        for item in value:
            if not self.inner_type(item)


class MappingValidator(ContainerValidator):
    def validate_contents(self, value):
        for item in value.items():
            self.inner_type(item)


class UnionValidator(Validator):
    def __init__(self, _type):
        self.args = [
            validator_for(t)
            for t in _type.__args__
        ]

    def __call__(self, value):
        if not any(
            arg.is_valid(value) for arg in self.args
        ):
            raise ValueError(f'{value !r} is not allowed type.')


def validator_for(_type):
    '''
    Utility function to create a Type validator callable.
    '''
    if isinstance(_type, typing._GenericAlias):
        base = _type.__origin__
        if issubclass(base, Container):
            if issubclass(base, Mapping):
                return MappingValidator(_type)
            return ContainerValidator(_type)
        elif issubclass(base, typing.Union):
            return UnionValidator(_type)
        # Optional, Any, AnyStr ?

    if any(
        issubclass(_type, x)
        for x in (str, int, float, set, dict, tuple, list)
    ):
        return SimpleValidator(_type)

    raise TypeError(f"How do I validate a {base !r} ?")


class NO_DEFAULT:
    pass


class SchemaProperty:
    def __init__(self, _type, default):
        self._type = _type
        self.default = default

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        try:
            return instance.__data__[self.name]
        except KeyError:
            if self.default is NO_DEFAULT:
                raise AttributeError(f'Schema {instance} has no value for {self.name}')

        return self.default

    def __set__(self, instance, value):
        if inspect.isclass(self._type) and issubclass(self._type, Schema):
            value = self._type(**value)
        elif isinstance(self._type, Validator):
            if not self._type.is_valid(value):
                raise ValueError(f'{instance.__class__.__name__}.{self.name} does not accept value {value !r}')
        instance.__data__[self.name] = value


class SchemaType(type):
    def __new__(cls, classname, bases, namespace, **kwargs):
        namespace['__data__'] = {}

        for name, _type in namespace.get('__annotations__', {}).items():
            if name.startswith('__') and name.endswith('__'):
                continue

            default = namespace.get(name, NO_DEFAULT)

            if isinstance(default, types.FunctionType):
                continue

            _type = validator_for(_type)

            namespace[name] = SchemaProperty(_type, default)

        return type.__new__(cls, classname, bases, namespace, **kwargs)


class Schema(object, metaclass=SchemaType):
    __slots__ = ()

    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)
