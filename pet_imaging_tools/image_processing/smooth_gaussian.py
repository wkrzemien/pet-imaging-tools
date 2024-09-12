#!/usr/bin/env python3
'''
Script to smooth the image with Gaussian filter.
As an input interfile header and smoothing filter are given.
Script assumes that the header (.hdr) and image files are in the same directory.
It is possible to determine the Gaussian filter for all three directions.
For further information, please refer to command python3 smooth_gaussian.py --help
'''

import argparse
import logging
import os
import shutil
from tempfile import mkstemp

import numpy as np
from scipy.ndimage import gaussian_filter
from pet_imaging_tools.image_processing.image_tools import get_info_from_interfile_header

logger = logging.getLogger(__name__)


def get_gauss_filter(filter_size):
  """
  Get the size of the gauss filter in all three dimensions.
  """
  if not ',' in filter_size:
    gauss_filter_mm = np.full(3, float(filter_size))

  else:
    gauss_filter_mm = filter_size.split(',')
    gauss_filter_mm = [float(i) for i in gauss_filter_mm]
    if len(gauss_filter_mm) == 2:
      gauss_filter_mm.insert(0, gauss_filter_mm[0])

  gauss_filter_mm = np.array(gauss_filter_mm)

  return gauss_filter_mm


def smooth_and_save_image(
    img_header, vol_name, matrix_size, data_type, gauss_filter_voxels
):
  """
  Smooth the original image, then save the smoothed image to a new file.
  """

  sep = img_header.split('/')[-1]
  filename = os.path.join(img_header.split(sep)[0], vol_name)

  image = np.fromfile(
      filename, dtype=data_type
  ).reshape(
      matrix_size, order='F'
  )

  logger.debug("Smoothing original image")
  img = gaussian_filter(image, sigma=gauss_filter_voxels)
  logger.debug("Saving smoothed image")
  img.flatten('F').astype(data_type
                          ).tofile(img_header.split('.')[0] + '_smooth.img')


def save_new_header(old_img_header, vol_name):
  """
  Write the new header to disk.
  """

  new_image_header = old_img_header.split('.')[0] + '_smooth.hdr'
  shutil.copyfile(old_img_header, new_image_header)

  file_descriptor, abs_path = mkstemp()
  with os.fdopen(file_descriptor, 'w') as new_file:
    with open(old_img_header, encoding="utf-8") as old_file:
      lines = old_file.readlines()
      for line in lines:
        splitted = line.split(' := ')
        splitted[0] = " ".join(splitted[0].split())
        if '!name of data file' in splitted[0]:
          new_file.write(
              '!name of data file := ' + vol_name.split('.')[0] +
              '_smooth.img' + '\n'
          )
        else:
          new_file.write(line)

  shutil.copymode(old_img_header, abs_path)
  shutil.move(abs_path, new_image_header)


def smooth_gaussian(old_img_header, filter_size):
  """
  Smooth an image with a Gaussian filter of given size.
  The filter can be of different size in all three dimensions.
  """

  logger.debug("Get image properties from original interfile")
  old_img_file, vox_size, matrix_size, dtype = get_info_from_interfile_header(
      old_img_header
  )

  gauss_filter_mm = get_gauss_filter(filter_size)
  gauss_filter_voxels = gauss_filter_mm / vox_size

  logger.debug("  Gaussian filter given in mm: %s", gauss_filter_mm)
  logger.debug("  Gaussian filter given in voxels: %s", gauss_filter_voxels)

  logger.debug(old_img_header)
  logger.debug(old_img_file)
  smooth_and_save_image(
      old_img_header, old_img_file, matrix_size, dtype, gauss_filter_voxels
  )

  logger.debug("Saving the new interfile header")
  save_new_header(old_img_header, old_img_file)


def main():
  """
  Parse arguments then run image smoothing.
  """
  parser = argparse.ArgumentParser(
      description='Simple script to smooth the image with Gaussian smoothing'
  )

  parser.add_argument(
      '--img_header', help='Interfile header path', required=True
  )

  parser.add_argument(
      '--filter_size',
      help="""
      Filter size (sigma) in mm. One, two or three values could be given separated by \',\', i.e.
      --filter_size 3.5 will smooth image the same sigma for all three axis
      --filter_size 3.5,5.0 will smooth image with sigma=3.5 mm in transaxial direction
      (x- and y-axis) and sigma=5.0 mm in axial direction(z-axis)
      --filter_size 3.5,5.0,6.0 will smooth image with various sigma in all three directions
      (3.5 mm in x-axis 5.0 mm in y-axis and 6.0 mm in z-axis)
      """,
      required=True
  )

  parser.add_argument(
      '--debug', help='Debug flag (default=False)', default='False'
  )

  args = parser.parse_args()

  old_img_header = args.img_header
  current_filter_size = args.filter_size

  debug = args.debug.lower() in ['true', '1', 'yes']

  if debug:
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')
  else:
    logging.basicConfig(level=logging.INFO, format='%(message)s')

  smooth_gaussian(old_img_header, current_filter_size)


if __name__ == '__main__':
  main()
