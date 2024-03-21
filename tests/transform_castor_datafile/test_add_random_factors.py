"""Tests for add_random_factors.py.
"""

import unittest
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from tests.helper_tools import download_file

from src.transform_castor_datafile.update_castor_datafile import write_row, get_flags, get_dtype, CASToRCDFField

from src.transform_castor_datafile.add_random_factors import *  # pylint: disable=unused-wildcard-import


class AddRandomFactors(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    remote_test_path = 'http://sphinx.if.uj.edu.pl/test_data/total-body-tools/transform_castor_datafile/'
    cls.test_folder = os.path.join(
        'tests', 'transform_castor_datafile', 'test_data'
    ) + '/'  # '/' is required by helper_tools.download_data. Probably we should remove it in the future
    os.makedirs(cls.test_folder, exist_ok=True)
    cls.lut_file = 'Modular'
    if not os.path.exists(os.path.join(cls.test_folder, cls.lut_file)):
      download_file(cls.lut_file, cls.test_folder, url=remote_test_path)
    cls.matrix_file = 'matrix.txt'
    if not os.path.exists(os.path.join(cls.test_folder, cls.matrix_file)):
      download_file(cls.matrix_file, cls.test_folder, url=remote_test_path)

  def test_add_random_factors(self):

    with tempfile.TemporaryDirectory() as tmp_dir:

      input_cdh = Path(tmp_dir) / 'test.Cdh'
      input_cdf = Path(tmp_dir) / 'test.Cdf'

      # duplicate code with add_normalization_factors
      with open(input_cdh, 'w', encoding='utf-8') as input_cdh_file:
        input_cdh_file.write(
            f'''Data filename: {input_cdf}
Number of events: 2
Data mode: list-mode
Data type: PET
Start time (s): 0
Duration (s): 100000
Scanner name: Modular
Calibration factor: 1
Isotope: unknown'''
        )

      row1 = pd.Series(
          {
              CASToRCDFField.TIMESTAMP: 1,
              CASToRCDFField.CRYSTAL_ID_1: 1,
              CASToRCDFField.CRYSTAL_ID_2: 2
          }
      )
      row2 = pd.Series(
          {
              CASToRCDFField.TIMESTAMP: 2,
              CASToRCDFField.CRYSTAL_ID_1: 45,
              CASToRCDFField.CRYSTAL_ID_2: 31
          }
      )
      with open(input_cdf, 'w+b') as input_cdf_file:
        write_row(row1, input_cdf_file)
        write_row(row2, input_cdf_file)

      output_cdh = Path(tmp_dir) / 'output.Cdh'
      output_cdf = Path(tmp_dir) / 'output.Cdf'

      input_lut_file = os.path.join(self.test_folder, self.lut_file)
      input_matrix_file = os.path.join(self.test_folder, self.matrix_file)

      add_random_factors_jmodular_24m50z(
          input_cdh, input_lut_file, input_matrix_file, output_cdh, output_cdf
      )

      with open(output_cdh, 'r+', encoding='utf-8') as cdh_file:
        cdh_content = cdh_file.read()
        self.assertTrue(
            read_cdh_field(cdh_content, CASToRCDHKey.RANDOM_CORRECTION_FLAG) ==
            '1'
        )

        flags = get_flags(cdh_content)
        cdf_dt = get_dtype(flags)

        with open(output_cdf, 'rb') as cdf_file:
          cdf_df = pd.DataFrame(np.frombuffer(cdf_file.read(), cdf_dt))
          self.assertTrue(cdf_df.iloc[0][CASToRCDFField.CRYSTAL_ID_1] == 1)
          self.assertTrue(cdf_df.iloc[0][CASToRCDFField.CRYSTAL_ID_2] == 2)
          self.assertTrue(
              np.abs(cdf_df.iloc[0][CASToRCDFField.RANDOM] - 0.3) < 1e-6
          )
          self.assertTrue(cdf_df.iloc[1][CASToRCDFField.CRYSTAL_ID_1] == 45)
          self.assertTrue(cdf_df.iloc[1][CASToRCDFField.CRYSTAL_ID_2] == 31)
          self.assertTrue(
              np.abs(cdf_df.iloc[1][CASToRCDFField.RANDOM] - 0.1875) < 1e-6
          )

  def test_add_random_field_present(self):

    with tempfile.TemporaryDirectory() as tmp_dir:

      input_cdf = Path(tmp_dir) / 'test.Cdf'
      input_cdf.touch()

      input_cdh = Path(tmp_dir) / 'test.Cdh'
      with open(input_cdh, 'w', encoding='utf-8') as input_cdh_file:
        input_cdh_file.write(
            f'''Data filename: {input_cdf}
Number of events: 2
Data mode: list-mode
Data type: PET
Start time (s): 0
Duration (s): 100000
Scanner name: Modular
Calibration factor: 1
Isotope: unknown
Random correction flag: 1'''

            # <--
        )

      output_cdh = Path(tmp_dir) / 'output.Cdh'
      output_cdf = Path(tmp_dir) / 'output.Cdf'

      input_lut_file = os.path.join(self.test_folder, self.lut_file)
      input_matrix_file = os.path.join(self.test_folder, self.matrix_file)

      self.assertRaises(
          ValueError, add_random_factors_jmodular_24m50z, input_cdh,
          input_lut_file, input_matrix_file, output_cdh, output_cdf
      )


if __name__ == '__main__':
  unittest.main()
