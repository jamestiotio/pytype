"""An abstract virtual machine for type analysis of python bytecode."""

from typing import Dict, Optional, Sequence

from pytype import config
from pytype.blocks import blocks
from pytype.pyc import pyc
from pytype.pytd import pytd
from pytype.pytd import pytd_utils
from pytype.rewrite import context
from pytype.rewrite import frame as frame_lib
from pytype.rewrite.abstract import abstract


class VirtualMachine:
  """Virtual machine."""

  def __init__(
      self,
      ctx: context.Context,
      code: blocks.OrderedCode,
      initial_globals: Dict[str, abstract.BaseValue],
  ):
    self._ctx = ctx
    self._code = code
    self._initial_globals = initial_globals
    self._module_frame: frame_lib.Frame = None

  @classmethod
  def from_source(
      cls, src: str, ctx: Optional[context.Context] = None,
  ) -> 'VirtualMachine':
    ctx = ctx or context.Context()
    code = _get_bytecode(src, ctx.options)
    initial_globals = ctx.abstract_loader.get_module_globals()
    return cls(ctx, code, initial_globals)

  def _run_module(self) -> None:
    assert not self._module_frame
    initial_global_vars = {name: val.to_variable()
                           for name, val in self._initial_globals.items()}
    self._module_frame = frame_lib.Frame.make_module_frame(
        self._ctx, self._code, initial_global_vars)
    self._module_frame.run()

  def analyze_all_defs(self) -> None:
    """Analyzes all class and function definitions."""
    self._run_module()
    parent_frames = [self._module_frame]
    while parent_frames:
      parent_frame = parent_frames.pop(0)
      for f in parent_frame.functions:
        parent_frames.extend(f.analyze())
      classes = _collect_classes(parent_frame)
      for cls in classes:
        instance = cls.instantiate()
        for f in cls.functions:
          parent_frames.extend(f.bind_to(instance).analyze())

  def infer_stub(self) -> pytd.TypeDeclUnit:
    """Infers a type stub."""
    self._run_module()
    pytd_nodes = []
    for name, value in self._module_frame.final_locals.items():
      if name in self._initial_globals and value == self._initial_globals[name]:
        continue
      try:
        pytd_node = value.to_pytd_def()
      except NotImplementedError:
        pytd_node = pytd.Constant(name, value.to_pytd_type())
      pytd_nodes.append(pytd_node)
    return pytd_utils.WrapTypeDeclUnit('inferred', pytd_nodes)


def _get_bytecode(src: str, options: config.Options) -> blocks.OrderedCode:
  code = pyc.compile_src(
      src=src,
      python_version=options.python_version,
      python_exe=options.python_exe,
      filename=options.input,
      mode='exec',
  )
  ordered_code, unused_block_graph = blocks.process_code(code)
  return ordered_code


def _collect_classes(
    frame: frame_lib.Frame) -> Sequence[abstract.InterpreterClass]:
  all_classes = []
  new_classes = list(frame.classes)
  while new_classes:
    cls = new_classes.pop(0)
    all_classes.append(cls)
    new_classes.extend(cls.classes)
  return all_classes
