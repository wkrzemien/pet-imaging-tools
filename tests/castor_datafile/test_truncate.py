"""Tests for truncate.py.
"""

import unittest
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from pet_imaging_tools.castor_datafile import write_row, get_flags, get_dtype, CASToRCDHKey, CASToRCDFField, read_cdh_field
from pet_imaging_tools.castor_datafile.truncate import truncate


class TruncateCASTORDatafile(unittest.TestCase):

  def test_truncate(self):

    with tempfile.TemporaryDirectory() as tmp_dir:

      input_cdh = Path(tmp_dir) / 'test.Cdh'
      input_cdf = Path(tmp_dir) / 'test.Cdf'
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
        for n in range(1, input_number_of_events + 1):
          write_row(
              {
                  CASToRCDFField.TIMESTAMP: n,
                  CASToRCDFField.CRYSTAL_ID_1: n,
                  CASToRCDFField.CRYSTAL_ID_2: n
              }, input_cdf_file
          )

      output_cdh = Path(tmp_dir) / 'output.Cdh'
      output_cdf = Path(tmp_dir) / 'output.Cdf'
      output_number_of_event = 10

      truncate(input_cdh, output_number_of_event, output_cdh, output_cdf)

      with open(output_cdh, 'r+', encoding='utf-8') as cdh_file:
        cdh_content = cdh_file.read()
        self.assertTrue(
            read_cdh_field(cdh_content, CASToRCDHKey.NUMBER_OF_EVENTS) ==
            str(output_number_of_event)
        )

        flags = get_flags(cdh_content)
        cdf_dt = get_dtype(flags)

        with open(output_cdf, 'rb') as cdf_file:
          cdf_df = pd.DataFrame(np.frombuffer(cdf_file.read(), cdf_dt))
          self.assertTrue(
              cdf_df.iloc[-1][CASToRCDFField.TIMESTAMP] ==
              output_number_of_event
          )
          self.assertTrue(
              cdf_df.iloc[-1][CASToRCDFField.CRYSTAL_ID_1] ==
              output_number_of_event
          )
          self.assertTrue(
              cdf_df.iloc[-1][CASToRCDFField.CRYSTAL_ID_2] ==
              output_number_of_event
          )


if __name__ == '__main__':
  unittest.main()
