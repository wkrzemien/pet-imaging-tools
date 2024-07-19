#!/usr/bin/env python3
"""
Truncate a CASToR datafile to keep only the first events.

This is useful for instance to reduce the size of a datafile to check if an operation correctly
terminates, before running the actual long computation.
"""

import re
import logging
import argparse

from pet_imaging_tools.castor_datafile import (
    update_castor_datafile, CASToRCDHKey, StopProcessingException
)


def truncate(cdh_path, number_of_events, output_cdh, output_cdf):
  """
  Truncate a CASToR datafile, keeping only the first events.

  Args:
    cdh_path (str): the CASToR header file.
    number_of_events (int): number of rows to keep.
    output_cdh (str): output CASToR header file.
    output_cdf (str): output CASToR data file.
  """

  def update_cdh(old_cdh):
    return re.sub(
        f'^{CASToRCDHKey.NUMBER_OF_EVENTS}:.*$',
        f'{CASToRCDHKey.NUMBER_OF_EVENTS}: {number_of_events}',
        old_cdh,
        flags=re.MULTILINE
    )

  i = 0

  def update_row(row):
    nonlocal i
    i = i + 1
    if i > number_of_events:
      raise StopProcessingException
    return row

  update_castor_datafile(
      cdh_path, output_cdh, output_cdf, update_cdh, update_row
  )


def parse_args():
  """
  Parse command-line arguments for truncate function.

  Returns:
    Parsed command-line arguments.
  """
  parser = argparse.ArgumentParser(description="Truncate a CASToR datafile.")
  parser.add_argument('--cdh', help="CASToR data header", required=True)
  parser.add_argument('--output-cdf', help="output Cdf file", required=True)
  parser.add_argument('--output-cdh', help="output Cdh file", required=True)
  parser.add_argument(
      '-n', help="number of rows to keep", type=int, required=True
  )
  return parser.parse_args()


def main():
  """
  Truncate a CASToR datafile by keeping only the first events.
  """
  logging.getLogger().setLevel(logging.INFO)
  args = parse_args()
  truncate(args.cdh, args.n, args.output_cdh, args.output_cdf)


if __name__ == '__main__':
  main()
