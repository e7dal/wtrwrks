import unittest
import reversible_transforms.utils.test_helpers as th
import reversible_transforms.tanks.max as mx
import numpy as np


class TestMax(th.TestTank):

  def test_one_d(self):
    self.pour_pump(
      mx.max,
      {'a': np.array([1, 3]), 'axis':()},
      {'target': np.array(3), 'a': np.array([1, 3]), 'axis': None},
      type_dict={'a': np.ndarray, 'axis': int}
    )

  def test_two_d(self):
    self.pour_pump(
      mx.max,
      {'a': np.array([[0, 1], [2, 3], [4, 5], [1, 0]]), 'axis': 1},
      {
        'target': np.array([1, 3, 5, 1]),
        'a': np.array([[0, 1], [2, 3], [4, 5], [1, 0]]),
        'axis': 1
      },
      type_dict={'a': np.ndarray, 'axis': int}
    )

    self.pour_pump(
      mx.max,
      {'a': np.array([[0, 1], [2, 3], [4, 5], [1, 0]]), 'axis': 0},
      {
        'target': np.array([4, 5]),
        'a': np.array([[0, 1], [2, 3], [4, 5], [1, 0]]),
        'axis': 0
      },
      type_dict={'a': np.ndarray, 'axis': int}
    )

  def test_three_d(self):
    self.pour_pump(
      mx.max,
      {'a': np.arange(24).reshape((2, 3, 4)), 'axis': (0, 1)},
      {
        'target': np.array([20, 21, 22, 23]),
        'a': np.arange(24).reshape((2, 3, 4)),
        'axis': (0, 1)
      },
      type_dict={'a': np.ndarray, 'axis': int}
    )

if __name__ == "__main__":
    unittest.main()
