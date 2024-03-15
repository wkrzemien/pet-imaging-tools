"""Tests if add_normalization_factors and add_random_factors are commutative.
"""
import os

import unittest
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from tests.helper_tools import download_file

from transform_castor_datafile.update_castor_datafile import write_row, get_flags, get_dtype, CASToRCDFField, read_cdh_field, CASToRCDHKey

from transform_castor_datafile.add_normalization_factors import add_normalization_factors
from transform_castor_datafile.add_random_factors import add_random_factors_jmodular_24m50z


class CorrectionFactorsCommutativity(unittest.TestCase):

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

  def test_add_nr_factors(self):

    with tempfile.TemporaryDirectory() as tmp_dir:

      input_cdh = Path(tmp_dir) / 'test.Cdh'
      input_cdf = Path(tmp_dir) / 'test.Cdf'
      input_nf = Path(tmp_dir) / 'nf.csv'

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

      with open(input_nf, 'w', encoding='utf-8') as input_nf_file:
        input_nf_file.write('''c1,c2,n
1,2,1.5
45,31,0.5''')

      temp_cdh = Path(tmp_dir) / 'temp.Cdh'
      temp_cdf = Path(tmp_dir) / 'temp.Cdf'

      output_cdh = Path(tmp_dir) / 'output.Cdh'
      output_cdf = Path(tmp_dir) / 'output.Cdf'

      input_lut_file = os.path.join(self.test_folder, self.lut_file)
      input_matrix_file = os.path.join(self.test_folder, self.matrix_file)

      add_normalization_factors(input_cdh, input_nf, temp_cdh, temp_cdf)
      add_random_factors_jmodular_24m50z(
          temp_cdh, input_lut_file, input_matrix_file, output_cdh, output_cdf
      )

      with open(output_cdh, 'r+', encoding='utf-8') as cdh_file:
        cdh_content = cdh_file.read()
        self.assertTrue(
            read_cdh_field(
                cdh_content, CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG
            ) == '1'
        )
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
          self.assertAlmostEqual(
              cdf_df.iloc[0][CASToRCDFField.NORMALIZATION], 1.5
          )
          self.assertAlmostEqual(cdf_df.iloc[0][CASToRCDFField.RANDOM], 0.3)
          self.assertTrue(cdf_df.iloc[1][CASToRCDFField.CRYSTAL_ID_1] == 45)
          self.assertTrue(cdf_df.iloc[1][CASToRCDFField.CRYSTAL_ID_2] == 31)
          self.assertAlmostEqual(
              cdf_df.iloc[1][CASToRCDFField.NORMALIZATION], .5
          )
          self.assertAlmostEqual(cdf_df.iloc[1][CASToRCDFField.RANDOM], 0.1875)

  def test_add_rn_factors(self):

    with tempfile.TemporaryDirectory() as tmp_dir:

      input_cdh = Path(tmp_dir) / 'test.Cdh'
      input_cdf = Path(tmp_dir) / 'test.Cdf'
      input_nf = Path(tmp_dir) / 'nf.csv'

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

      with open(input_nf, 'w', encoding='utf-8') as input_nf_file:
        input_nf_file.write('''c1,c2,n
1,2,1.5
45,31,0.5''')

      temp_cdh = Path(tmp_dir) / 'temp.Cdh'
      temp_cdf = Path(tmp_dir) / 'temp.Cdf'

      output_cdh = Path(tmp_dir) / 'output.Cdh'
      output_cdf = Path(tmp_dir) / 'output.Cdf'

      input_lut_file = os.path.join(self.test_folder, self.lut_file)
      input_matrix_file = os.path.join(self.test_folder, self.matrix_file)

      add_random_factors_jmodular_24m50z(
          input_cdh, input_lut_file, input_matrix_file, temp_cdh, temp_cdf
      )
      add_normalization_factors(temp_cdh, input_nf, output_cdh, output_cdf)

      with open(output_cdh, 'r+', encoding='utf-8') as cdh_file:
        cdh_content = cdh_file.read()
        self.assertTrue(
            read_cdh_field(
                cdh_content, CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG
            ) == '1'
        )
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
          self.assertAlmostEqual(
              cdf_df.iloc[0][CASToRCDFField.NORMALIZATION], 1.5
          )
          self.assertAlmostEqual(cdf_df.iloc[0][CASToRCDFField.RANDOM], 0.3)
          self.assertTrue(cdf_df.iloc[1][CASToRCDFField.CRYSTAL_ID_1] == 45)
          self.assertTrue(cdf_df.iloc[1][CASToRCDFField.CRYSTAL_ID_2] == 31)
          self.assertAlmostEqual(
              cdf_df.iloc[1][CASToRCDFField.NORMALIZATION], .5
          )
          self.assertAlmostEqual(cdf_df.iloc[1][CASToRCDFField.RANDOM], 0.1875)


if __name__ == '__main__':
  unittest.main()
