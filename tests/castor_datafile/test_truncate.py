"""Tests for truncate.py.
"""

import numpy as np
import pandas as pd

from pet_imaging_tools.castor_datafile import (
    write_row, get_flags, get_dtype, CASToRCDHKey, CASToRCDFField,
    read_cdh_field
)
from pet_imaging_tools.castor_datafile.truncate import truncate


def test_truncate(tmp_path):
  """
  Test the CLI tools to truncate CASToR datafiles.
  """

  input_cdh = tmp_path / 'test.Cdh'
  input_cdf = tmp_path / 'test.Cdf'
  input_number_of_events = 20

  with open(input_cdh, 'w', encoding='utf-8') as input_cdh_file:
    input_cdh_file.write(
        f'''Data filename: {input_cdf}
Number of events: {input_number_of_events}
Data mode: list-mode
Data type: PET
Start time (s): 0
Duration (s): 100000
Scanner name: Modular
Calibration factor: 1
Isotope: unknown'''
    )

  with open(input_cdf, 'w+b') as input_cdf_file:
    for i in range(1, input_number_of_events + 1):
      write_row(
          {
              CASToRCDFField.TIMESTAMP: i,
              CASToRCDFField.CRYSTAL_ID_1: i,
              CASToRCDFField.CRYSTAL_ID_2: i
          }, input_cdf_file
      )

  output_cdh = tmp_path / 'output.Cdh'
  output_cdf = tmp_path / 'output.Cdf'
  output_number_of_event = 10

  truncate(input_cdh, output_number_of_event, output_cdh, output_cdf)

  with open(output_cdh, 'r+', encoding='utf-8') as cdh_file:
    cdh_content = cdh_file.read()
    assert read_cdh_field(cdh_content, CASToRCDHKey.NUMBER_OF_EVENTS
                          ) == str(output_number_of_event)

    cdf_dt = get_dtype(get_flags(cdh_content))
    with open(output_cdf, 'rb') as cdf_file:
      cdf_df = pd.DataFrame(np.frombuffer(cdf_file.read(), cdf_dt))
      assert cdf_df.iloc[-1][CASToRCDFField.TIMESTAMP
                             ] == output_number_of_event
      assert cdf_df.iloc[-1][CASToRCDFField.CRYSTAL_ID_1
                             ] == output_number_of_event
      assert cdf_df.iloc[-1][CASToRCDFField.CRYSTAL_ID_2
                             ] == output_number_of_event
