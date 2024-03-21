"""Add pre-computed normalization factors to a CASToR data file (*.Cdf).

Normalization factors are assumed to be in the form of a CSV file with following header:
c1,c2,n

This script can also serves as a skeleton on how to use update_castor_datafile.py.
"""

import argparse
import logging
import os

import pandas as pd

from src.transform_castor_datafile.update_castor_datafile import update_castor_datafile, read_cdh_field, CASToRCDHKey, CASToRCDFField


def add_normalization_factors(cdh_path, nf, output_cdh, output_cdf):
  """Add normalization factors from a CSV file to a pair of CASToR header/data file.

  Args:
    cdh_path (str): the CASToR header file.
    nf (str): the CSV file that contains normalization factors.
    output_cdh (str): output CASToR header file.
    output_cdf (str): output CASToR data file.
  """

  nf_df = pd.read_csv(nf, index_col=[0, 1])
  logging.info(f"Successfully read {nf}.")

  def update_cdh(old_cdh):
    if read_cdh_field(old_cdh,
                      CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG) == '1':
      raise ValueError("File already contains normalization data.")

    return old_cdh + (
        '' if old_cdh.endswith(os.linesep) else os.linesep
    ) + CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG + ': 1'

  def update_row(row):
    try:
      nf = nf_df.loc[row[CASToRCDFField.CRYSTAL_ID_1],
                     row[CASToRCDFField.CRYSTAL_ID_2]]['n']
    except KeyError:  # the corresponding normalization factor does not exist
      nf = 1.
    row[CASToRCDFField.NORMALIZATION] = nf
    return row

  update_castor_datafile(
      cdh_path, output_cdh, output_cdf, update_cdh, update_row
  )


def parse_args():
  """Parse command-line arguments.

  Returns:
    Parsed command-line arguments.
  """
  parser = argparse.ArgumentParser(
      description="Add normalization factors to a CASToR data file (*.Cdf)."
  )
  parser.add_argument('--cdh', help="CASToR data header", required=True)
  parser.add_argument('--nf', help="normalizatiom factors", required=True)
  parser.add_argument('--output-cdf', help="output Cdf file", required=True)
  parser.add_argument('--output-cdh', help="output Cdh file", required=True)
  return parser.parse_args()


def main():
  """Add normalization factors to a CASToR data file (*.Cdf).
  """

  logging.getLogger().setLevel(logging.INFO)

  args = parse_args()

  add_normalization_factors(
      args.cdh, args.nf, args.output_cdh, args.output_cdf
  )


if __name__ == '__main__':
  main()
