#!/usr/bin/env python3
""" Several methods to load an image and generate some X,Y,Z and XY, XZ, YZ profiles and estimate Full Width Half Maximum of the peak.
  The calculations of fwhm are done according to NEMA standard, using linear approximation and using Gaussian fit, respectively.
"""

import argparse
import logging
import os
import sys
import lzma

from math import floor
from scipy.optimize import curve_fit

import numpy as np
import matplotlib.pyplot as plt
import gatetools as gt

LOGGER = logging.getLogger(__name__)


def get_info_from_interfile_header(header_file):
  """Gets information from the interfile header file.

  Args:
    header_file (str): Name of the input  header file in the interfile format,
                       alternatively compressed with lzma.
  Returns:
    tuple: f_name (str), voxel_size(list), matrix_size (list), dtype(str)
    with the following meaning:
    f_name is the name of the image file in the interfile format,
    voxel_size is the list of voxel sizes in mm along X,Y and Z axis,
    matrix_size is the list corresponding to the image size along X,Y and Z direction.
    dtype is the string corresponding to the numpy format of numbers in the image matrix

  Examples:
    returned values:  "recon_true_230ps_it1.img", [2.4, 2.4, 2.4], [220, 220, 280], 'float32'

  """
  f_name = ''
  matrix_size = [0, 0, 0]
  voxel_size = [0., 0., 0.]

  if os.path.splitext(header_file)[1] == '.xz':
    my_open = lzma.open
  else:
    my_open = open
  with my_open(header_file, 'rt', encoding="utf-8") as my_file:
    lines = my_file.readlines()
    for line in lines:
      splitted = line.split(' := ')
      splitted[0] = " ".join(splitted[0].split())
      if splitted[0] == '!name of data file':
        f_name = splitted[1].rstrip("\n")
      elif splitted[0].startswith(
          '!matrix size [') and splitted[0][-1] == ']' and splitted[0][-2] in (
              '1', '2', '3'):
        matrix_size[int(splitted[0][-2]) - 1] = int(splitted[1])
      elif splitted[0].startswith('scaling factor (mm/pixel) [') and splitted[
          0][-1] == ']' and splitted[0][-2] in ('1', '2', '3'):
        voxel_size[int(splitted[0][-2]) - 1] = float(splitted[1])
      elif splitted[0] == '!number format':
        if 'float' in splitted[1]:
          ttype = 'float'
        else:
          ttype = 'int'
      elif splitted[0] == '!number of bytes per pixel':
        nbytes = 8 * int(splitted[1])

    dtype = ttype + str(nbytes)

  LOGGER.debug("\tData file name: %s", f_name)
  LOGGER.debug("\tImage dimensions: %s", str(matrix_size))
  LOGGER.debug("\tVoxel size: %s", str(voxel_size))

  return f_name, voxel_size, matrix_size, dtype


def load_image_and_metadata(
    header_file, las_convention=False, return_dicom_properties: bool = False
):
  """Gets metadata and the image file based on the information in the header file.
  Args:
    header_file (str): Name of the input  header file in the interfile format,
                       alternatively compressed with lzma.
    las_convention (bool): If set to true try to load the image in the radiological LAS convention (Left Anterior Superior).
                           Uses C matrix ordering convention and flips the image. Default is set to false.
    return_dicom_properties If set to True return tuple (image_matrix, dicom_properties)
                            where dicom propertis is a tuple (matrix_size, voxel_size, dicom_origin)
                            if set to False (default option) return tuple (image_matrix, voxel_size, matrix_size)

  Returns:
    tuple: image_matrix (numpy.array), voxel_size(list), matrix_size (list)   if return_dicom_properties = False
    tuple  image_matrix (numpy.array), dicom_properties (touple)              if return_dicom_properties = True


    with the following meaning:
    dicom_properties is tuple: matrix_size, voxel_size, dicom_origin
    image_matrix is the numpy.array 3-D matrix contaning the image intensities,
    voxel_size is the list of voxel sizes in mm along X,Y and Z axis,
    matrix_size is the list corresponding to the image size along X,Y and Z direction.
    dicom origin is np.array which corresponds to origin due to dicom standard


  Examples:
    returned values: numpy.array, [2.4, 2.4, 2.4], [220, 220, 280]    if return_dicom_properties = False
    returned values: numpy.array, ([220, 220, 280], [2.4, 2.4, 2.4], [-108.8,-108.8,-138.8]) if return_dicom_properties = True
  """
  load_order = 'F'
  if las_convention:
    load_order = 'C'

  path = os.path.dirname(os.path.abspath(header_file))
  image_file, voxel_size, matrix_size, data_type = get_info_from_interfile_header(
      header_file
  )
  image_file = os.path.join(path, image_file)
  if las_convention:
    matrix_size = np.flip(matrix_size)
  if os.path.splitext(header_file)[1] == '.xz':
    image_file = image_file + ".xz"
    with lzma.open(image_file, "rb") as image_data:
      # https://github.com/numpy/numpy/issues/10866
      image_matrix = np.frombuffer(image_data.read(), dtype=data_type)
  else:
    image_matrix = np.fromfile(image_file, dtype=data_type)
  image_matrix = image_matrix.reshape(matrix_size, order=load_order)
  if las_convention:
    image_matrix = np.flip(image_matrix)

  if return_dicom_properties is False:
    return (image_matrix, voxel_size, matrix_size)

  dicom_origin = get_dicom_origin(matrix_size, voxel_size, img_center=None)
  dicom_properties_object = gt.dicom_properties()
  dicom_properties_object.spacing = voxel_size  # only if gap = 0; probably don't work propely in MRI \
  dicom_properties_object.origin = dicom_origin
  dicom_properties_object.image_shape = matrix_size

  return (image_matrix, dicom_properties_object)


def get_dicom_origin(vector_size, vector_voxel_size, img_center=None):
  """get dicom orgin based for image size, voxel_size, and image center.
  Args:
        vector_size (np.array): 3-elements vector;size of image in voxels
        vector_voxel_size (np.array): 3-elements vector; size of voxels in mm
        center(np.array | list | tuple): 3-elements vector; center of the lab coordinate system in voxels,
                                         default value is the image centre
  Returns:
        numpy.array (lu_voxel-center) : 3-elements vector; position in mm of the first voxel center [0,0,0]
                                        in the lab coordinate system.

  Examples:
    returned values: [-30.0,-15.5,20.2]
  """
  img_size = np.array(vector_size)
  voxel_size = np.array(vector_voxel_size)
  center_mm = 0

  lu_voxel_center_mm = np.divide(voxel_size, 2.0)

  if img_center is None:

    center_mm = (img_size / 2.0) * voxel_size
  else:
    center_mm = (img_center) * voxel_size
  return lu_voxel_center_mm - center_mm


def transform_interfile_header(input_header, output_header, transform_list):
  """Copy an interfile header to another file and edit some of its field on the way.

  Args:
    input_header (str): Name of the input header file in the interfile format.
    output_header (str): Name of the output header file.
    transform_list (list(tuple(str, str))): list of (field, value) tuples.

  Example:
    transform_interfile_header('xcat.hdr', 'xcat_rescaled.hdr', ['data rescale slope', str(2)])
  """
  with open(input_header, 'r', encoding='utf-8') as input_file, open(
      output_header, 'w', encoding='utf-8') as output_file:
    input_header_lines = input_file.readlines()
    for line in input_header_lines:
      splitted = line.split(' := ')
      splitted[0] = " ".join(splitted[0].split())
      for t in transform_list:
        if t[0] in splitted[0]:
          output_file.write(f'{t[0]} := {t[1]}' + os.linesep)
          break
      else:
        output_file.write(line)

