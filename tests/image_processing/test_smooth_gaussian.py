""" Unit tests for smooth_gaussian
"""
import unittest
import os
import sys
from tests.helper_tools import download_file
from pet_imaging_tools.image_processing.smooth_gaussian import smooth_gaussian

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# pylint: disable=protected-access, missing-docstring, invalid-name, line-too-long


class Test_smooth_gaussian(unittest.TestCase):

  def setUp(self):
    self.thisDir = os.path.dirname(os.path.abspath(__file__))
    self.input_header_file = self.thisDir + '/recon_true_230ps_it1.hdr'
    self.input_image_file = self.thisDir + '/recon_true_230ps_it1.img'
    self.output_header_file = self.thisDir + '/recon_true_230ps_it1_smooth.hdr'
    self.output_image_file = self.thisDir + '/recon_true_230ps_it1_smooth.img'

    if not os.path.exists(self.input_image_file):
      download_file('recon_true_230ps_it1.img', self.thisDir + '/')

    if not os.path.exists(self.input_header_file):
      download_file('recon_true_230ps_it1.hdr', self.thisDir + '/')

    try:
      os.remove(self.output_header_file)
      os.remove(self.output_image_file)
    except OSError:
      pass

  def tearDown(self):
    try:
      os.remove(self.output_header_file)
      os.remove(self.output_image_file)
    except OSError:
      pass

  def test_success(self):
    in_header = os.path.join(self.thisDir, self.input_header_file)
    smooth_gaussian(in_header, "3.5")
    self.assertTrue(os.path.exists(self.output_image_file))
    self.assertTrue(os.path.exists(self.output_header_file))


if __name__ == '__main__':
  suite = unittest.defaultTestLoader.loadTestsFromTestCase(
      Test_smooth_gaussian
  )
  testResult = unittest.TextTestRunner(verbosity=2).run(suite)
