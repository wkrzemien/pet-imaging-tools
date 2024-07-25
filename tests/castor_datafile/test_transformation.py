"""Tests for transformation.py.
"""

import filecmp
import os
import tempfile

from unittest import mock
import pytest

import pandas as pd
import numpy as np

from pet_imaging_tools.castor_datafile import (
    read_cdh_field, get_cdf_path, check_flag, get_dtype, get_flags,
    is_list_mode, max_nb_of_lines_per_event, replace_cdh_field,
    update_castor_datafile, write_row, CASToRCDHKey, CASToRCDFField, UINT32_T,
    FLTNBDATA
)

DEFAULT_CDH_CONTENT = """Data filename: sensitivity_lm_Modular_df.Cdf
Number of events: 3609862611
Data mode: list-mode
Data type: PET
Start time (s): 0
Duration (s): 100000
Scanner name: Modular
Calibration factor: 1
Isotope: unknown"""


def test_read_cdh_field():
  """
  Tests of reading of header files.
  """

  # Normal example
  assert read_cdh_field(DEFAULT_CDH_CONTENT, "Calibration factor") == "1"

  # Non-existing field
  assert read_cdh_field(DEFAULT_CDH_CONTENT, "Non-existing") is None

  # Empty file
  assert read_cdh_field("", "Non-existing") is None

  # Field defined twice
  with pytest.raises(ValueError):
    read_cdh_field(
        DEFAULT_CDH_CONTENT + """
Calibration factor: 2""", "Calibration factor"
    )

  # White spaces
  assert read_cdh_field(
      DEFAULT_CDH_CONTENT + """
    Test:     abc     """, "Test"
  ) == "abc"


def test_replace_cdh_field():
  """
 Tests of updating header fields.
  """

  # Normal example
  assert replace_cdh_field(
      DEFAULT_CDH_CONTENT, CASToRCDHKey.DATA_FILENAME, 'test.Cdf'
  ) == """Data filename: test.Cdf
Number of events: 3609862611
Data mode: list-mode
Data type: PET
Start time (s): 0
Duration (s): 100000
Scanner name: Modular
Calibration factor: 1
Isotope: unknown"""

  # Non-existent field
  assert replace_cdh_field(
      DEFAULT_CDH_CONTENT, 'Non-existent', 'new value'
  ) == DEFAULT_CDH_CONTENT


def test_is_list_mode():
  """
  Test if list-mode check is properly handled.
  """

  # Normal example
  assert is_list_mode(DEFAULT_CDH_CONTENT)

  # Histogram data
  assert not is_list_mode(
      """Data filename: sensitivity_lm_Modular_df.Cdf
Number of events: 3609862611
Data mode: histogram
Data type: PET
Start time (s): 0
Duration (s): 100000"""
  )

  # Field missing
  with pytest.raises(ValueError):
    is_list_mode(
        """Data filename: sensitivity_lm_Modular_df.Cdf
Number of events: 3609862611
Data type: PET
Start time (s): 0
Duration (s): 100000"""
    )


def test_check_flag():
  """
  Test if flags are properly handled from CASToR header file.
  """

  # Normal example
  assert not check_flag(
      DEFAULT_CDH_CONTENT, CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG
  )

  # Flag set to 1
  assert check_flag(
      """Data filename: sensitivity_lm_Modular_df.Cdf
Number of events: 3609862611
Data mode: histogram
Data type: PET
Start time (s): 0
Normalization correction flag: 1""", CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG
  )

  # Flag set to 0
  assert not check_flag(
      """Data filename: sensitivity_lm_Modular_df.Cdf
Number of events: 3609862611
Data mode: histogram
Data type: PET
Start time (s): 0
Normalization correction flag: 0""", CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG
  )

  # Flag set to 2
  assert check_flag(
      """Data filename: sensitivity_lm_Modular_df.Cdf
Number of events: 3609862611
Data mode: histogram
Data type: PET
Start time (s): 0
Normalization correction flag: 2""", CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG
  )

  # Flag set to erroneous value
  with pytest.raises(ValueError):
    check_flag(
        """Data filename: sensitivity_lm_Modular_df.Cdf
Number of events: 3609862611
Data mode: histogram
Data type: PET
Start time (s): 0
Normalization correction flag: hello""",
        CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG
    )


def test_get_flags():
  """
  Test if flags are properly read from CASToR header file.
  """

  # Normal example
  assert get_flags(DEFAULT_CDH_CONTENT) == {
      CASToRCDHKey.ATTENUATION_CORRECTION_FLAG: False,
      CASToRCDHKey.SCATTER_CORRECTION_FLAG: False,
      CASToRCDHKey.RANDOM_CORRECTION_FLAG: False,
      CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG: False,
      CASToRCDHKey.TOF_INFORMATION_FLAG: False
  }

  # With normalization
  assert get_flags(
      """Data filename: sensitivity_lm_Modular_df.Cdf
Number of events: 3609862611
Data mode: histogram
Data type: PET
Start time (s): 0
Normalization correction flag: 1"""
  ) == {
      CASToRCDHKey.ATTENUATION_CORRECTION_FLAG: False,
      CASToRCDHKey.SCATTER_CORRECTION_FLAG: False,
      CASToRCDHKey.RANDOM_CORRECTION_FLAG: False,
      CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG: True,
      CASToRCDHKey.TOF_INFORMATION_FLAG: False
  }


def test_max_nb_of_lines_per_event():
  """
  Check if maximum number of lines is properly read from CASToR header.
  """

  # Normal example
  assert max_nb_of_lines_per_event(DEFAULT_CDH_CONTENT) == 1

  # Another number
  assert max_nb_of_lines_per_event(
      DEFAULT_CDH_CONTENT + """
Maximum number of lines per event: 2"""
  ) == 2

  # Not a number
  with pytest.raises(ValueError):
    max_nb_of_lines_per_event(
        DEFAULT_CDH_CONTENT + """
Maximum number of lines per event: toto"""
    )


def test_cdf_path():
  """
    Test if path to binary datafiles is correctly read.
    """
  cdh_content = f"""{CASToRCDHKey.DATA_FILENAME}: c"""
  with mock.patch('os.path.dirname') as mock_dirname:
    mock_dirname.return_value = '/a/b'
    assert get_cdf_path(cdh_content, 'test.Cdh') == '/a/b/c'


def test_get_dtype():
  """
  Check if datatypes are properly generated.
  """

  # All false
  assert get_dtype(
      {
          CASToRCDHKey.ATTENUATION_CORRECTION_FLAG: False,
          CASToRCDHKey.SCATTER_CORRECTION_FLAG: False,
          CASToRCDHKey.RANDOM_CORRECTION_FLAG: False,
          CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG: False,
          CASToRCDHKey.TOF_INFORMATION_FLAG: False
      }
  ) == [
      (CASToRCDFField.TIMESTAMP, UINT32_T),
      (CASToRCDFField.CRYSTAL_ID_1, UINT32_T),
      (CASToRCDFField.CRYSTAL_ID_2, UINT32_T)
  ]

  # All true
  assert get_dtype(
      {
          CASToRCDHKey.ATTENUATION_CORRECTION_FLAG: True,
          CASToRCDHKey.SCATTER_CORRECTION_FLAG: True,
          CASToRCDHKey.RANDOM_CORRECTION_FLAG: True,
          CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG: True,
          CASToRCDHKey.TOF_INFORMATION_FLAG: True
      }
  ) == [
      (CASToRCDFField.TIMESTAMP, UINT32_T),
      (CASToRCDFField.ATTENUATION, FLTNBDATA),
      (CASToRCDFField.SCATTER, FLTNBDATA), (CASToRCDFField.RANDOM, FLTNBDATA),
      (CASToRCDFField.NORMALIZATION, FLTNBDATA),
      (CASToRCDFField.TOF, FLTNBDATA), (CASToRCDFField.CRYSTAL_ID_1, UINT32_T),
      (CASToRCDFField.CRYSTAL_ID_2, UINT32_T)
  ]


def test_write_row():
  """
  Test if rows are properly written to CASToR binary datafile.
  """
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
      assert row[field] == read_row[field]


def test_update_castor_datafile(tmp_path):
  """
  Test if updating a CASToR datafile runs without throwing any error.
  """

  input_cdh = tmp_path / 'test.Cdh'
  input_cdf = tmp_path / 'test.Cdf'

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

  output_cdh = tmp_path / 'output.Cdh'
  output_cdf = tmp_path / 'output.Cdf'

  update_castor_datafile(input_cdh, output_cdh, output_cdf)

  with open(input_cdh, 'r+', encoding='utf-8') as input_cdh_file:
    input_cdh_content = input_cdh_file.read()
    input_cdh_content_normalized = input_cdh_content.replace(
        str(input_cdf),
        os.path.split(output_cdf)[1]
    )
    with open(output_cdh, 'r+', encoding='utf-8') as output_cdh_file:
      output_cdh_content = output_cdh_file.read()
      assert input_cdh_content_normalized == output_cdh_content

  assert filecmp.cmp(input_cdf, output_cdf)
