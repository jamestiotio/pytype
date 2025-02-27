"""Overlays on top of abstract values that provide extra typing information.

An overlay generates extra typing information that cannot be expressed in a pyi
file. For example, collections.namedtuple is a factory method that generates
class definitions at runtime. An overlay is used to generate these classes.
"""
from typing import Callable, Dict, Tuple, Type, TypeVar

from pytype.rewrite.abstract import abstract

_FuncTypeType = Type[abstract.PytdFunction]
_FuncTypeTypeT = TypeVar('_FuncTypeTypeT', bound=_FuncTypeType)

FUNCTIONS: Dict[Tuple[str, str], _FuncTypeType] = {}


def register_function(
    module: str, name: str) -> Callable[[_FuncTypeTypeT], _FuncTypeTypeT]:
  def register(func_builder: _FuncTypeTypeT) -> _FuncTypeTypeT:
    FUNCTIONS[(module, name)] = func_builder
    return func_builder
  return register


def initialize():
  # Imports overlay implementations so that ther @register_* decorators execute
  # and populate the overlay registry.
  # pylint: disable=g-import-not-at-top,unused-import
  # pytype: disable=import-error
  from pytype.rewrite.overlays import enum_overlay
  from pytype.rewrite.overlays import special_builtins
  # pytype: enable=import-error
  # pylint: enable=g-import-not-at-top,unused-import
