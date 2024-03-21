"""Tests for add_normalization_factors.py.
"""

import unittest
import tempfile
from pathlib import Path

import numpy as np

from src.transform_castor_datafile.update_castor_datafile import write_row, get_flags, get_dtype, CASToRCDFField

from src.transform_castor_datafile.add_normalization_factors import *  # pylint: disable=unused-wildcard-import


class AddNormalizationFactors(unittest.TestCase):

  def test_add_normalization_factors(self):

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
              CASToRCDFField.CRYSTAL_ID_1: 2,
              CASToRCDFField.CRYSTAL_ID_2: 1
          }
      )
      with open(input_cdf, 'w+b') as input_cdf_file:
        write_row(row1, input_cdf_file)
        write_row(row2, input_cdf_file)

      with open(input_nf, 'w', encoding='utf-8') as input_nf_file:
        input_nf_file.write('''c1,c2,n
1,2,1.5
2,1,0.5''')

      output_cdh = Path(tmp_dir) / 'output.Cdh'
      output_cdf = Path(tmp_dir) / 'output.Cdf'

      add_normalization_factors(input_cdh, input_nf, output_cdh, output_cdf)

      with open(output_cdh, 'r+', encoding='utf-8') as cdh_file:
        cdh_content = cdh_file.read()
        self.assertTrue(
            read_cdh_field(
                cdh_content, CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG
            ) == '1'
        )

        flags = get_flags(cdh_content)
        cdf_dt = get_dtype(flags)

        with open(output_cdf, 'rb') as cdf_file:
          cdf_df = pd.DataFrame(np.frombuffer(cdf_file.read(), cdf_dt))
          self.assertTrue(cdf_df.iloc[0][CASToRCDFField.CRYSTAL_ID_1] == 1)
          self.assertTrue(cdf_df.iloc[0][CASToRCDFField.CRYSTAL_ID_2] == 2)
          self.assertTrue(
              np.abs(cdf_df.iloc[0][CASToRCDFField.NORMALIZATION] - 1.5) < 1e-9
          )
          self.assertTrue(cdf_df.iloc[1][CASToRCDFField.CRYSTAL_ID_1] == 2)
          self.assertTrue(cdf_df.iloc[1][CASToRCDFField.CRYSTAL_ID_2] == 1)
          self.assertTrue(
              np.abs(cdf_df.iloc[1][CASToRCDFField.NORMALIZATION] - .5) < 1e-9
          )

  def test_add_nf_field_present(self):

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
Normalization correction flag: 1'''

            # <--
        )

      input_nf = Path(tmp_dir) / 'nf.csv'
      input_nf.touch()

      output_cdh = Path(tmp_dir) / 'output.Cdh'
      output_cdf = Path(tmp_dir) / 'output.Cdf'

      self.assertRaises(
          ValueError, add_normalization_factors, input_cdh, input_nf,
          output_cdh, output_cdf
      )


if __name__ == '__main__':
  unittest.main()
