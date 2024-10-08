"""Tests for replicate.py.
"""

import tempfile
from pathlib import Path

import pytest

import numpy as np
import pandas as pd

from pet_imaging_tools.castor_datafile import write_row, get_flags, get_dtype, CASToRCDFField
from pet_imaging_tools.castor_datafile.replicate import replicate


def test_replicate(tmp_path):
  """
  Test if CLI tool replicate correctly operates.
  """

  input_cdh = tmp_path / 'test.Cdh'
  input_cdf = tmp_path / 'test.Cdf'
  n_rows = 10

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
    for i in range(n_rows):
      write_row(
          {
              CASToRCDFField.TIMESTAMP: i,
              CASToRCDFField.CRYSTAL_ID_1: i,
              CASToRCDFField.CRYSTAL_ID_2: i
          }, input_cdf_file
      )

  output_cdh = tmp_path / 'output.Cdh'
  output_cdf = tmp_path / 'output.Cdf'

  replicate(input_cdh, output_cdh, output_cdf)

  with open(output_cdh, 'r+', encoding='utf-8') as cdh_file:

    cdh_content = cdh_file.read()
    flags = get_flags(cdh_content)
    cdf_dt = get_dtype(flags)

    with open(output_cdf, 'rb') as cdf_file:
      cdf_df = pd.DataFrame(np.frombuffer(cdf_file.read(), cdf_dt))
      # We check only the length, as the content of the file is random random
      assert len(cdf_df) == n_rows


def test_replicate_file_not_found():
  """
  Test that when the user tries to replicate a datafile that does not exist, the user gets an error
  message.
  """

  with tempfile.TemporaryDirectory() as tmp_dir:

    input_cdh = Path(tmp_dir) / 'nonexistent.Cdh'
    output_cdh = Path(tmp_dir) / 'output_nonexistent.Cdh'
    output_cdf = Path(tmp_dir) / 'output_nonexistent.Cdf'

    with pytest.raises(SystemExit):
      replicate(input_cdh, output_cdh, output_cdf)
