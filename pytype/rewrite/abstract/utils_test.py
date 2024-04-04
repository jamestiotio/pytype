from typing import Tuple

from pytype.rewrite.abstract import base
from pytype.rewrite.abstract import classes
from pytype.rewrite.abstract import utils
from pytype.rewrite.tests import test_utils
from typing_extensions import assert_type

import unittest


class GetAtomicConstantTest(test_utils.ContextfulTestBase):

  def test_get(self):
    var = classes.PythonConstant(self.ctx, 'a').to_variable()
    const = utils.get_atomic_constant(var)
    self.assertEqual(const, 'a')

  def test_get_with_type(self):
    var = classes.PythonConstant(self.ctx, 'a').to_variable()
    const = utils.get_atomic_constant(var, str)
    assert_type(const, str)
    self.assertEqual(const, 'a')

  def test_get_with_bad_type(self):
    var = classes.PythonConstant(self.ctx, 'a').to_variable()
    with self.assertRaisesRegex(ValueError, 'expected int, got str'):
      utils.get_atomic_constant(var, int)

  def test_get_with_parameterized_type(self):
    var = classes.PythonConstant(self.ctx, ('a',)).to_variable()
    const = utils.get_atomic_constant(var, Tuple[str, ...])
    assert_type(const, Tuple[str, ...])
    self.assertEqual(const, ('a',))

  def test_get_with_bad_parameterized_type(self):
    var = classes.PythonConstant(self.ctx, 'a').to_variable()
    with self.assertRaisesRegex(ValueError, 'expected tuple, got str'):
      utils.get_atomic_constant(var, Tuple[str, ...])


class JoinValuesTest(test_utils.ContextfulTestBase):

  def test_empty(self):
    self.assertEqual(utils.join_values(self.ctx, []), self.ctx.singles.Any)

  def test_one_value(self):
    a = classes.PythonConstant(self.ctx, 'a')
    self.assertEqual(utils.join_values(self.ctx, [a]), a)

  def test_multiple_values(self):
    a = classes.PythonConstant(self.ctx, 'a')
    b = classes.PythonConstant(self.ctx, 'b')
    val = utils.join_values(self.ctx, [a, b])
    self.assertEqual(val, base.Union(self.ctx, (a, b)))


if __name__ == '__main__':
  unittest.main()
