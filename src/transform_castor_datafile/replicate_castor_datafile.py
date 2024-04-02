"""
Replicate CASToR data file using sampling with repetition on ensemble of rows from the original
file (*.Cdf).
We operate on list-mode data format.
"""

import logging
import os
import sys

from src.transform_castor_datafile.utils import default_parser

from src.transform_castor_datafile.update_castor_datafile import get_cdf_and_cdh_content_from_file
from src.transform_castor_datafile.update_castor_datafile import write_new_cdh_file
from src.transform_castor_datafile.update_castor_datafile import write_new_cdf_file


def replicate_castor_datafile(cdh_path, output_cdh, output_cdf):
  """Replicates a pair of CASToR header/data file.

  Args:
    cdh_path (str): the CASToR header file.
    output_cdh (str): output CASToR header file.
    output_cdf (str): output CASToR data file.
  """
  try:
    cdh_content, cdf_dd = get_cdf_and_cdh_content_from_file(cdh_path)
    cdf_filename = os.path.split(output_cdf)[1]
    replicated_cdf = cdf_dd.sample(frac=1.0, replace=True)
    write_new_cdh_file(output_cdh, cdf_filename, cdh_content)
    write_new_cdf_file(output_cdf, replicated_cdf)

  except FileNotFoundError as file_not_found:
    logging.error("File not found: %s.", file_not_found.filename)
    sys.exit(1)


def parse_args():
  """Parse command-line arguments.

  Returns:
    Parsed command-line arguments.
  """
  parser = default_parser("Replicate CASToR data file (*.Cdf).")
  return parser.parse_args()


def main():
  """Replicate CASToR data file (*.Cdf) using the sampling with repetition.
  """

  logging.getLogger().setLevel(logging.INFO)

  args = parse_args()

  replicate_castor_datafile(args.cdh, args.output_cdh, args.output_cdf)


if __name__ == '__main__':
  main()
