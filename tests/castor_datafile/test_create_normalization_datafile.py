"""Tests for add_normalization_factors.py.
"""

import pytest

import numpy as np
import pandas as pd

from pet_imaging_tools.castor_datafile import (
    write_row, get_flags, get_dtype, CASToRCDHKey, CASToRCDFField,
    read_cdh_field, FLTNBDATA, UINT32_T
)
from pet_imaging_tools.castor_datafile.create_normalization_datafile import create_normalization_datafile


def test_create_normalization_datafile(tmp_path):
  """
  Test for CLI tool to create normalization datafile.
  """

  input_nf = tmp_path / 'nf.csv'

  with open(input_nf, 'w', encoding='utf-8') as input_nf_file:
    input_nf_file.write('''c1,c2,n
1,2,1.5
2,3,0.5''')

  output = str(tmp_path / 'output')
  output_cdh = output + '.Cdh'
  output_cdf = output + '.Cdf'

  create_normalization_datafile(str(input_nf), 4, output)

  with open(output_cdh, 'r+', encoding='utf-8') as cdh_file:

    cdh_content = cdh_file.read()
    assert read_cdh_field(cdh_content, 'Data mode') == 'normalization'

  dtype = [('n', FLTNBDATA), ('c1', UINT32_T), ('c2', UINT32_T)]
  cdf_np = np.fromfile(output_cdf, dtype=dtype)
  expected = np.array(
      [
          (1., 0, 1), (1., 0, 2), (1., 0, 3), (1.5, 1, 2), (1., 1, 3),
          (0.5, 2, 3)
      ],
      dtype=dtype
  )
  assert np.array_equal(cdf_np, expected)
