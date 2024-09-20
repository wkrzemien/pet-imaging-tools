"""
Unit tests for function_to_image.
"""

import os
import numpy as np

from pet_imaging_tools.image_processing.function_to_image import function_to_image


def test_function_to_image_empty(tmp_path):
  """
  Test if an empty image is properly generated with a constant function f(x,y,z)=0.
  """
  out = os.path.join(tmp_path, 'test')
  function_to_image(out, 'empty')
  arr = np.fromfile(out + '.raw')
  assert np.allclose(arr, 0.)
