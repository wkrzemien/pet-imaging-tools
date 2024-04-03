"""Tests for transformation.py.
"""

import tempfile
import unittest
import filecmp
import os
from unittest import mock
from pathlib import Path

import pandas as pd
import numpy as np

from pet_imaging_tools.castor_datafile.transformation import read_cdh_field, get_cdf_path, check_flag, get_dtype, get_flags, is_list_mode, max_nb_of_lines_per_event, replace_cdh_field, update_castor_datafile, write_row, CASToRCDHKey, CASToRCDFField, UINT32_T, FLTNBDATA


class UpdateCASToRDatafile(unittest.TestCase):

  default_cdh_content = """Data filename: sensitivity_lm_Modular_df.Cdf
Number of events: 3609862611
Data mode: list-mode
Data type: PET
Start time (s): 0
Duration (s): 100000
Scanner name: Modular
Calibration factor: 1
Isotope: unknown"""

  def test_read_cdf_field(self):

    # Normal example
    self.assertEqual(
        read_cdh_field(self.default_cdh_content, "Calibration factor"), "1"
    )

    # Non-existing field
    self.assertEqual(
        read_cdh_field(self.default_cdh_content, "Non-existing"), None
    )

    # Empty file
    self.assertEqual(read_cdh_field("", "Non-existing"), None)

    # Field defined twice
    self.assertRaises(
        ValueError, read_cdh_field, self.default_cdh_content + """
Calibration factor: 2""", "Calibration factor"
    )

    # White spaces
    self.assertEqual(
        read_cdh_field(
            self.default_cdh_content + """
Test:     abc     """, "Test"
        ), "abc"
    )

  def test_replace_cdh_field(self):

    # Normal example
    self.assertEqual(
        replace_cdh_field(
            self.default_cdh_content, CASToRCDHKey.DATA_FILENAME, 'test.Cdf'
        ), """Data filename: test.Cdf
Number of events: 3609862611
Data mode: list-mode
Data type: PET
Start time (s): 0
Duration (s): 100000
Scanner name: Modular
Calibration factor: 1
Isotope: unknown"""
    )

    # Non-existent field
    self.assertEqual(
        replace_cdh_field(
            self.default_cdh_content, 'Non-existent', 'new value'
        ), self.default_cdh_content
    )

  def test_is_list_mode(self):

    # Normal example
    self.assertTrue(is_list_mode(self.default_cdh_content))

    # Histogram data
    self.assertFalse(
        is_list_mode(
            """Data filename: sensitivity_lm_Modular_df.Cdf
Number of events: 3609862611
Data mode: histogram
Data type: PET
Start time (s): 0
Duration (s): 100000"""
        )
    )

    # Field missing
    self.assertRaises(
        ValueError, is_list_mode,
        """Data filename: sensitivity_lm_Modular_df.Cdf
Number of events: 3609862611
Data type: PET
Start time (s): 0
Duration (s): 100000"""
    )

  def test_check_flag(self):

    # Normal example
    self.assertFalse(
        check_flag(
            self.default_cdh_content,
            CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG
        )
    )

    # Flag set to 1
    self.assertTrue(
        check_flag(
            """Data filename: sensitivity_lm_Modular_df.Cdf
Number of events: 3609862611
Data mode: histogram
Data type: PET
Start time (s): 0
Normalization correction flag: 1""", CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG
        )
    )

    # Flag set to 0
    self.assertFalse(
        check_flag(
            """Data filename: sensitivity_lm_Modular_df.Cdf
Number of events: 3609862611
Data mode: histogram
Data type: PET
Start time (s): 0
Normalization correction flag: 0""", CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG
        )
    )

    # Flag set to 2
    self.assertTrue(
        check_flag(
            """Data filename: sensitivity_lm_Modular_df.Cdf
Number of events: 3609862611
Data mode: histogram
Data type: PET
Start time (s): 0
Normalization correction flag: 2""", CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG
        )
    )

    # Flag set to erroneous value
    self.assertRaises(
        ValueError, check_flag, """Data filename: sensitivity_lm_Modular_df.Cdf
Number of events: 3609862611
Data mode: histogram
Data type: PET
Start time (s): 0
Normalization correction flag: hello""",
        CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG
    )

  def test_get_flags(self):

    # Normal example
    self.assertEqual(
        get_flags(self.default_cdh_content), {
            CASToRCDHKey.ATTENUATION_CORRECTION_FLAG: False,
            CASToRCDHKey.SCATTER_CORRECTION_FLAG: False,
            CASToRCDHKey.RANDOM_CORRECTION_FLAG: False,
            CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG: False,
            CASToRCDHKey.TOF_INFORMATION_FLAG: False
        }
    )

    # With normalization
    self.assertEqual(
        get_flags(
            """Data filename: sensitivity_lm_Modular_df.Cdf
Number of events: 3609862611
Data mode: histogram
Data type: PET
Start time (s): 0
Normalization correction flag: 1"""
        ), {
            CASToRCDHKey.ATTENUATION_CORRECTION_FLAG: False,
            CASToRCDHKey.SCATTER_CORRECTION_FLAG: False,
            CASToRCDHKey.RANDOM_CORRECTION_FLAG: False,
            CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG: True,
            CASToRCDHKey.TOF_INFORMATION_FLAG: False
        }
    )

  def test_max_nb_of_lines_per_event(self):

    # Normal example
    self.assertEqual(max_nb_of_lines_per_event(self.default_cdh_content), 1)

    # Another number
    self.assertEqual(
        max_nb_of_lines_per_event(
            self.default_cdh_content + """
Maximum number of lines per event: 2"""
        ), 2
    )

    # Not a number
    self.assertRaises(
        ValueError, max_nb_of_lines_per_event, self.default_cdh_content + """
Maximum number of lines per event: toto"""
    )

  def test_cdf_path(self):
    cdh_content = f"""{CASToRCDHKey.DATA_FILENAME}: c"""
    with mock.patch('os.path.dirname') as mock_dirname:
      mock_dirname.return_value = '/a/b'

      self.assertEqual(get_cdf_path(cdh_content, 'test.Cdh'), '/a/b/c')

  def test_get_dtype(self):

    # All false
    self.assertEqual(
        get_dtype(
            {
                CASToRCDHKey.ATTENUATION_CORRECTION_FLAG: False,
                CASToRCDHKey.SCATTER_CORRECTION_FLAG: False,
                CASToRCDHKey.RANDOM_CORRECTION_FLAG: False,
                CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG: False,
                CASToRCDHKey.TOF_INFORMATION_FLAG: False
            }
        ), [
            (CASToRCDFField.TIMESTAMP, UINT32_T),
            (CASToRCDFField.CRYSTAL_ID_1, UINT32_T),
            (CASToRCDFField.CRYSTAL_ID_2, UINT32_T)
        ]
    )

    # All true
    self.assertEqual(
        get_dtype(
            {
                CASToRCDHKey.ATTENUATION_CORRECTION_FLAG: True,
                CASToRCDHKey.SCATTER_CORRECTION_FLAG: True,
                CASToRCDHKey.RANDOM_CORRECTION_FLAG: True,
                CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG: True,
                CASToRCDHKey.TOF_INFORMATION_FLAG: True
            }
        ), [
            (CASToRCDFField.TIMESTAMP, UINT32_T),
            (CASToRCDFField.ATTENUATION, FLTNBDATA),
            (CASToRCDFField.SCATTER, FLTNBDATA),
            (CASToRCDFField.RANDOM, FLTNBDATA),
            (CASToRCDFField.NORMALIZATION, FLTNBDATA),
            (CASToRCDFField.TOF, FLTNBDATA),
            (CASToRCDFField.CRYSTAL_ID_1, UINT32_T),
            (CASToRCDFField.CRYSTAL_ID_2, UINT32_T)
        ]
    )

  def test_write_row(self):
    row = pd.Series(
        {
            CASToRCDFField.TIMESTAMP: 1,
            CASToRCDFField.CRYSTAL_ID_1: 1,
            CASToRCDFField.CRYSTAL_ID_2: 2
        }
    )
    dtypes = get_dtype({})  # no flags

    with tempfile.TemporaryFile() as cdf:
      write_row(row, cdf)
      cdf.seek(0)
      read_row = pd.DataFrame(np.frombuffer(cdf.read(), dtypes)).iloc[0]
      read_row.name = None  # to ensure comparison with row

      for field in [CASToRCDFField.TIMESTAMP, CASToRCDFField.CRYSTAL_ID_1,
                    CASToRCDFField.CRYSTAL_ID_2]:
        self.assertTrue(row[field] == read_row[field])

  def test_update_castor_datafile(self):

    with tempfile.TemporaryDirectory() as tmp_dir:

      input_cdh = Path(tmp_dir) / 'test.Cdh'
      input_cdf = Path(tmp_dir) / 'test.Cdf'

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

      row1 = {
          CASToRCDFField.TIMESTAMP: 1,
          CASToRCDFField.CRYSTAL_ID_1: 1,
          CASToRCDFField.CRYSTAL_ID_2: 2
      }

      row2 = {
          CASToRCDFField.TIMESTAMP: 2,
          CASToRCDFField.CRYSTAL_ID_1: 2,
          CASToRCDFField.CRYSTAL_ID_2: 1
      }

      with open(input_cdf, 'w+b') as input_cdf_file:
        write_row(row1, input_cdf_file)
        write_row(row2, input_cdf_file)

      output_cdh = Path(tmp_dir) / 'output.Cdh'
      output_cdf = Path(tmp_dir) / 'output.Cdf'

      update_castor_datafile(input_cdh, output_cdh, output_cdf)

      with open(input_cdh, 'r+', encoding='utf-8') as input_cdh_file:
        input_cdh_content = input_cdh_file.read()
        input_cdh_content_normalized = input_cdh_content.replace(
            str(input_cdf),
            os.path.split(output_cdf)[1]
        )
        with open(output_cdh, 'r+', encoding='utf-8') as output_cdh_file:
          output_cdh_content = output_cdh_file.read()
          self.assertTrue(input_cdh_content_normalized, output_cdh_content)

      self.assertTrue(filecmp.cmp(input_cdf, output_cdf))


if __name__ == '__main__':
  unittest.main()
