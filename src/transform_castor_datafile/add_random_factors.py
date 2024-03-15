"""Add pre-computed random correction factors to a CASToR data file (*.Cdf).

Random correction factors are assumed to be in the form of a TXT file containg
random correction probability matrix with assumed division of tomograph into sections.
Based on said division, the following code needs to be modified or extended to enable
correct assignemnt between given LOR and its projection in the matrix.

"""

import argparse
import logging
import os

import numpy as np

from transform_castor_datafile.update_castor_datafile import update_castor_datafile, read_cdh_field, CASToRCDHKey, CASToRCDFField


def get_module_from_hit(x, y):
  """Get ID of module in which the hit occured
    Works under assumption of counter-clockwise ID increment, and with ID=0 in 1st quadrant just above x-axis
    """
  unit_vec = np.array([1, 0])
  hit_vec = np.array([x, y])
  dot = unit_vec @ hit_vec
  det = unit_vec[0] * hit_vec[1] - unit_vec[1] * hit_vec[0]  # determinant
  angle = (np.degrees(np.arctan2(det, dot))) % 360
  no_modules = 24
  angle_modules_step = 360 / no_modules
  return angle // angle_modules_step


def add_random_factors_jmodular_24m50z(
    cdh_path, lut_name, map_name, output_cdh, output_cdf
):
  """Add random correction factors from a random correction matrix TXT file and using LUT file to a pair of CASToR header/data file.

  Args:
    cdh_path (str): the CASToR header file.
    lut_name (str): the LUT geoemtry file.
    map_name (str): the TXT file that contains random correction factors in a matrix form.
    output_cdh (str): output CASToR header file.
    output_cdf (str): output CASToR data file.
  """

  lut = np.fromfile(lut_name, dtype='float32').reshape((62400, 6))
  logging.info(f"Successfully read {lut_name}.")
  random_map = np.fromfile(
      map_name, dtype='float32', sep=' '
  ).reshape((1200, 1200))
  logging.info(f"Successfully read {map_name}.")

  def update_cdh(old_cdh):
    if read_cdh_field(old_cdh, CASToRCDHKey.RANDOM_CORRECTION_FLAG) == '1':
      raise ValueError("File already contains random correction data.")

    return old_cdh + (
        '' if old_cdh.endswith(os.linesep) else os.linesep
    ) + CASToRCDHKey.RANDOM_CORRECTION_FLAG + ': 1'

  def update_row(row):
    try:
      c_min = min(
          row[CASToRCDFField.CRYSTAL_ID_1], row[CASToRCDFField.CRYSTAL_ID_2]
      )
      c_max = max(
          row[CASToRCDFField.CRYSTAL_ID_1], row[CASToRCDFField.CRYSTAL_ID_2]
      )
      x1, y1, z1, _, _, _ = lut[c_min]
      x2, y2, z2, _, _, _ = lut[c_max]
      module1 = get_module_from_hit(x1, y1)
      module2 = get_module_from_hit(x2, y2)
      afov = 500
      z_sections_no = 50
      z_sections_size = afov / z_sections_no
      pos1 = z_sections_no * module1 + (z1 + afov / 2) // z_sections_size
      pos2 = z_sections_no * module2 + (z2 + afov / 2) // z_sections_size
      rf = random_map[int(pos1)][int(pos2)]
    except KeyError:  # the corresponding random correction factor does not exist
      rf = 0.
    row[CASToRCDFField.RANDOM] = rf
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
      description="Add random correction factors to a CASToR data file (*.Cdf)."
  )
  parser.add_argument('--cdh', help="CASToR data header", required=True)
  parser.add_argument('--lut-name', help="LUT geometry file", required=True)
  parser.add_argument(
      '--map-name',
      help="random correction factors matrix TXT file",
      required=True
  )
  parser.add_argument('--output-cdf', help="output Cdf file", required=True)
  parser.add_argument('--output-cdh', help="output Cdh file", required=True)
  return parser.parse_args()


def main():
  """Add random correction factors to a CASToR data file (*.Cdf).
  """

  logging.getLogger().setLevel(logging.INFO)

  args = parse_args()

  add_random_factors_jmodular_24m50z(
      args.cdh, args.lut_name, args.map_name, args.output_cdh, args.output_cdf
  )


if __name__ == '__main__':
  main()
