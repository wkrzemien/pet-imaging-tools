#!/usr/bin/env python3
"""
Add pre-computed normalization factors to a CASToR data file (*.Cdf).

Normalization factors are input in the form of a CSV file with following header:
c1,c2,n
where c1 and c2 are the crystal IDs, and n is the corresponding normalization factor.

For instance, the following file:
c1,c2,n
1,2,0.5
2,3,1.5
means that the LOR between crystal 1 and crystal 2 will receive a normalization factor of 0.5,
and that the LOR between crystal 2 and crystal 3 will receive a normalization factor of 1.5.

LORs absent from the CSV file will receive a default value of 1.

The CASToR header will also be updated. If the input file already contains normalization data, an
error will be raised and no transformation will be carried out.

The script is non-destructive, meaning that it creates a copy of the input CASToR datafile instead
of operating in-place. Thus, it should not destroy the original datafile.
"""

import logging
import os
import argparse

import pandas as pd

from pet_imaging_tools.castor_datafile import (
    update_castor_datafile, read_cdh_field, CASToRCDHKey, CASToRCDFField
)


def add_normalization_factors(cdh_path, nf_csv, output_cdh, output_cdf):
  """
  Add normalization factors from a CSV file to a pair of CASToR header/data file.

  Args:
    cdh_path (str): the CASToR header file.
    nf_csv (str): the CSV file that contains normalization factors.
    output_cdh (str): output CASToR header file.
    output_cdf (str): output CASToR data file.
  """

  nf_df = pd.read_csv(nf_csv, index_col=[0, 1])
  logging.info("Successfully read %s.", nf_csv)

  def update_cdh(old_cdh):
    if read_cdh_field(old_cdh,
                      CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG) == '1':
      raise ValueError("File already contains normalization data.")

    return old_cdh + (
        '' if old_cdh.endswith(os.linesep) else os.linesep
    ) + CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG + ': 1'

  def update_row(row):
    try:
      normalization_factor = nf_df.loc[row[CASToRCDFField.CRYSTAL_ID_1],
                                       row[CASToRCDFField.CRYSTAL_ID_2]]['n']
    except KeyError:  # the corresponding normalization factor does not exist
      normalization_factor = 1.
    row[CASToRCDFField.NORMALIZATION] = normalization_factor
    return row

  update_castor_datafile(
      cdh_path, output_cdh, output_cdf, update_cdh, update_row
  )


def parse_args():
  """
  Parse command-line arguments for add_normalization_factors function.

  Returns:
    Parsed command-line arguments.
  """
  parser = argparse.ArgumentParser(
      description="Add normalization factors to a CASToR data file (*.Cdf)."
  )
  parser.add_argument('--cdh', help="CASToR data header", required=True)
  parser.add_argument('--output-cdf', help="output Cdf file", required=True)
  parser.add_argument('--output-cdh', help="output Cdh file", required=True)
  parser.add_argument('--nf', help="normalizatiom factors", required=True)
  return parser.parse_args()


def main():
  """
  Add normalization factors to a CASToR datafile.
  """

  logging.getLogger().setLevel(logging.INFO)

  args = parse_args()

  add_normalization_factors(
      args.cdh, args.nf, args.output_cdh, args.output_cdf
  )


if __name__ == '__main__':
  main()
