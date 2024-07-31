""" Unit tests for function_to_image
"""

import unittest
import os
import sys
import tempfile
import numpy as np

from pet_imaging_tools.image_processing.function_to_image import function_to_image

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# pylint: disable=protected-access, missing-docstring, invalid-name, line-too-long


class Test_function_to_image(unittest.TestCase):

  def test_function_to_image_empty(self):
    with tempfile.TemporaryDirectory() as tmp:
      out = os.path.join(tmp, 'test')
      function_to_image(out, 'empty')
      arr = np.fromfile(out + '.raw')
      self.assertTrue(np.allclose(arr, 0.))


if __name__ == '__main__':
  suite = unittest.defaultTestLoader.loadTestsFromTestCase(
      Test_function_to_image
  )
  testResult = unittest.TextTestRunner(verbosity=2).run(suite)
