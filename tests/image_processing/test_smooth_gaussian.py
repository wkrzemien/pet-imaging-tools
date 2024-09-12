"""
Unit tests for smooth_gaussian.
"""

from pathlib import Path
import os

import pytest

from tests.helper_tools import download_file
from pet_imaging_tools.image_processing.smooth_gaussian import smooth_gaussian


@pytest.fixture(name='test_data')
def test_data_fixture():
  """
  Path to a directory used for temporary cached test files.
  """
  test_data = 'test_data'
  os.makedirs(test_data, exist_ok=True)
  return Path(test_data)


def test_smooth_gaussian(test_data):
  """
  Test function smooth_gaussian.
  """

  input_header_file = test_data / 'recon_true_230ps_it1.hdr'
  input_image_file = test_data / 'recon_true_230ps_it1.img'
  output_header_file = test_data / 'recon_true_230ps_it1_smooth.hdr'
  output_image_file = test_data / 'recon_true_230ps_it1_smooth.img'

  if not os.path.exists(input_image_file):
    download_file('recon_true_230ps_it1.img', str(test_data))

  if not os.path.exists(input_header_file):
    download_file('recon_true_230ps_it1.hdr', str(test_data))

  try:
    os.remove(output_header_file)
    os.remove(output_image_file)
  except OSError:
    pass

  smooth_gaussian(str(input_header_file), "3.5")

  assert os.path.exists(output_image_file)
  assert os.path.exists(output_header_file)
