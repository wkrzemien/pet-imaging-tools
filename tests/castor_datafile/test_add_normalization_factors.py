"""Tests for add_normalization_factors.py.
"""

import pytest

import numpy as np
import pandas as pd

from pet_imaging_tools.castor_datafile import (
    write_row, get_flags, get_dtype, CASToRCDHKey, CASToRCDFField,
    read_cdh_field
)
from pet_imaging_tools.castor_datafile.add_normalization_factors import add_normalization_factors


def test_add_normalization_factors(tmp_path):
  """
  Test for CLI tool to add normalization factors to CASToR datafile.
  """

  input_cdh = tmp_path / 'test.Cdh'
  input_cdf = tmp_path / 'test.Cdf'
  input_nf = tmp_path / 'nf.csv'

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

  with open(input_cdf, 'w+b') as input_cdf_file:
    write_row(
        pd.Series(
            {
                CASToRCDFField.TIMESTAMP: 1,
                CASToRCDFField.CRYSTAL_ID_1: 1,
                CASToRCDFField.CRYSTAL_ID_2: 2
            }
        ), input_cdf_file
    )
    write_row(
        pd.Series(
            {
                CASToRCDFField.TIMESTAMP: 2,
                CASToRCDFField.CRYSTAL_ID_1: 2,
                CASToRCDFField.CRYSTAL_ID_2: 1
            }
        ), input_cdf_file
    )

  with open(input_nf, 'w', encoding='utf-8') as input_nf_file:
    input_nf_file.write('''c1,c2,n
1,2,1.5
2,1,0.5''')

  output_cdh = tmp_path / 'output.Cdh'
  output_cdf = tmp_path / 'output.Cdf'

  add_normalization_factors(input_cdh, input_nf, output_cdh, output_cdf)

  with open(output_cdh, 'r+', encoding='utf-8') as cdh_file:
    cdh_content = cdh_file.read()
    assert read_cdh_field(
        cdh_content, CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG
    ) == '1'

    cdf_dt = get_dtype(get_flags(cdh_content))
    with open(output_cdf, 'rb') as cdf_file:
      cdf_df = pd.DataFrame(np.frombuffer(cdf_file.read(), cdf_dt))
      assert cdf_df.iloc[0][CASToRCDFField.CRYSTAL_ID_1] == 1
      assert cdf_df.iloc[0][CASToRCDFField.CRYSTAL_ID_2] == 2
      assert np.isclose(cdf_df.iloc[0][CASToRCDFField.NORMALIZATION], 1.5)
      assert cdf_df.iloc[1][CASToRCDFField.CRYSTAL_ID_1] == 2
      assert cdf_df.iloc[1][CASToRCDFField.CRYSTAL_ID_2] == 1
      assert np.isclose(cdf_df.iloc[1][CASToRCDFField.NORMALIZATION], .5)


def test_add_nf_field_present(tmp_path):
  """
  Check that when adding normalization factors to a file that already contains them, the user gets
  an error message.
  """

  input_cdf = tmp_path / 'test.Cdf'
  input_cdf.touch()

  input_cdh = tmp_path / 'test.Cdh'
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
    )

  input_nf = tmp_path / 'nf.csv'
  input_nf.touch()

  output_cdh = tmp_path / 'output.Cdh'
  output_cdf = tmp_path / 'output.Cdf'

  with pytest.raises(ValueError):
    add_normalization_factors(input_cdh, input_nf, output_cdh, output_cdf)
