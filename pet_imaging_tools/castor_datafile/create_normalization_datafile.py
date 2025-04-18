"""
Tool to generate a CASToR normalization datafile from a CSV file containing normalization factors.
"""

import argparse
import os
import logging
import sys

import numpy as np
import pandas as pd

from tqdm import tqdm

from pet_imaging_tools.castor_datafile.transformation import FLTNBDATA, UINT32_T


def process_lor(crystal_id_1, crystal_id_2, norm_df, cdf_file):
  """
  Process a single LOR.
  """

  try:
    norm_factor = norm_df.loc[crystal_id_1, crystal_id_2]['n']
  except KeyError:
    norm_factor = 1.

  cdf_file.write(np.dtype(FLTNBDATA).type(norm_factor))
  cdf_file.write(np.dtype(UINT32_T).type(crystal_id_1))
  cdf_file.write(np.dtype(UINT32_T).type(crystal_id_2))


def write_header(output, cdf_filename, n_events):
  """
  Write CASToR header.
  """
  cdh_filename = output + '.Cdh'
  logging.info("Writing %s…", cdh_filename)
  with open(cdh_filename, 'w', encoding='utf-8') as cdh_file:
    cdh_file.write('Scanner name: Modular' + os.linesep)
    cdh_file.write(
        f'Data filename: {os.path.basename(cdf_filename)}' + os.linesep
    )
    cdh_file.write(f'Number of events: {n_events}' + os.linesep)
    cdh_file.write('Data mode: normalization' + os.linesep)
    cdh_file.write('Data type: PET' + os.linesep)
    cdh_file.write(
        'Start time (s): 0' + os.linesep
    )  # Ignored for normalization mode
    cdh_file.write(
        'Duration (s): 1' + os.linesep
    )  # Ignored for normalization mode
    cdh_file.write('Normalization correction flag: 1' + os.linesep)


def create_normalization_datafile(
    norm, number_of_crystals, output, start=None, size=None
):
  """
  Write to CASToR file.
  """

  norm_df = pd.read_csv(norm, index_col=[0, 1])

  # Write data
  cdf_filename = output + '.Cdf'
  print(f"Writing {cdf_filename}…")

  if start is None or size is None:
    if (start is None) ^ (size is None):
      sys.exit("Both --start and --size must be set, or none of them.")
    crystal_id_1_range = range(number_of_crystals)
  else:
    crystal_id_1_range = range(start, start + size)

  n_events = 0
  with open(cdf_filename, 'w+b') as cdf_file:
    for crystal_id_1 in tqdm(crystal_id_1_range):
      crystal_id_2_range = range(crystal_id_1 + 1, number_of_crystals)
      for crystal_id_2 in crystal_id_2_range:
        process_lor(crystal_id_1, crystal_id_2, norm_df, cdf_file)
      n_events += len(crystal_id_2_range)

  write_header(output, cdf_filename, n_events)


def parse_args():
  """
  Parse arguments.
  """
  parser = argparse.ArgumentParser()

  parser.add_argument(
      '--norm', help="normalization factors file", required=True
  )
  parser.add_argument(
      '--number-of-crystals',
      help="number of crystals",
      required=True,
      type=int
  )
  parser.add_argument('-o', '--output', help="output file name", required=True)

  batch_group = parser.add_argument_group("batch processing")
  batch_group.add_argument(
      '--start', help="crystal ID to start from", type=int
  )
  batch_group.add_argument('--size', help="size of batch", type=int)

  return parser.parse_args()


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  args = parse_args()
  create_normalization_datafile(
      args.norm, args.number_of_crystals, args.output, args.start, args.size
  )
