from functools import reduce
from typing import Callable, Iterable, TypeVar

A = TypeVar("A")
B = TypeVar("B")


def flatmap(f: Callable[[A], Iterable[B]], xs: Iterable[A]) -> Iterable[B]:
    """ Map f over an iterable and flatten the result set.
    """
    return (y for x in xs for y in f(x))


def compose(*functions: Callable) -> Callable:
    """ Compose a variable # of functions.
    """
    return reduce(lambda f, g: lambda x: f(g(x)), functions[::-1], lambda x: x)
