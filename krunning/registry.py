from typing import TypeVar, Generic, Type, Dict, Callable, Iterable, Tuple

T = TypeVar("T")


class Registry(Generic[T]):
    def __init__(self):
        self.__elements: Dict[str, Type[T]] = {}

    def register(self, name: str) -> Callable[[Type[T]], Type[T]]:
        def register(cls: Type[T]):
            self.__elements[name] = cls
            return cls

        return register

    def __getitem__(self, name: str) -> Type[T]:
        return self.__elements[name]

    def items(self) -> Iterable[Tuple[str, Type[T]]]:
        return self.__elements.items()
