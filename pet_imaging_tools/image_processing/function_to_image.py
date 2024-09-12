#!/usr/bin/env python3
"""Convert an analytical function to an image file."""

import argparse
import logging
import os

from tqdm import tqdm
import numpy as np

from pet_imaging_tools.image_processing.functions.fov_sensitivity import fov_sensitivity

# Default values for Modular
VOXEL_SIZE = (2.5, 2.5, 2.5)
IMAGE_DIMENSION_MM = (800, 800, 500)

FUNCTIONS = {
    'empty':
        lambda x, y, z: 0,
    'fov_sensitivity':
        fov_sensitivity(IMAGE_DIMENSION_MM[0] // 2, IMAGE_DIMENSION_MM[2])
}


def function_to_image(output, fn_name):
  """Convert an analytic function to an image file."""

  image_dimensions_vx = [
      int(dim / size) for dim, size in zip(IMAGE_DIMENSION_MM, VOXEL_SIZE)
  ]
  logging.info("Image dimensions: %s (voxels)", image_dimensions_vx)

  center_image_vx = [dim // 2 for dim in image_dimensions_vx]
  logging.info("Center of the image: %s (voxels)", center_image_vx)

  ijk_to_xyz = lambda *ijk: [
      (i - c) * v + v / 2 for i, c, v in zip(ijk, center_image_vx, VOXEL_SIZE)
  ]
  fun = lambda *ijk: FUNCTIONS[fn_name](*ijk_to_xyz(*ijk))
  img_np = np.array(
      [
          [
              [fun(i, j, k)
               for k in range(image_dimensions_vx[2])]
              for j in range(image_dimensions_vx[1])
          ]
          for i in tqdm(range(image_dimensions_vx[1]))
      ]
  )
  logging.info("Computed matrix: %s", img_np)

  header_path = output + ".hdr"
  raw_path = output + ".raw"
  raw_name = os.path.basename(raw_path)

  write_header(header_path, raw_name, img_np)
  write_raw(raw_path, img_np)


def write_header(header_path, raw_name, img_np):
  """
  Write header file of the function converted to an image.
  """
  with open(header_path, 'w', encoding='utf-8') as file:
    file.write(
        f'''!name of data file := {raw_name}
file.write('!total number of images := 1
file.write('imagedata byte order := LITTLEENDIAN
file.write('number of dimensions := 3
file.write(f'!matrix size [1] := {img_np.shape[0]}
file.write(f'!matrix size [2] := {img_np.shape[1]}
file.write(f'!matrix size [3] := {img_np.shape[2]}
file.write('!number format := float
file.write('!number of bytes per pixel := 4
file.write(f'scaling factor (mm/pixel) [1] := {VOXEL_SIZE[0]}
file.write(f'scaling factor (mm/pixel) [2] := {VOXEL_SIZE[1]}
file.write(f'scaling factor (mm/pixel) [3] := {VOXEL_SIZE[2]}
file.write('image duration (sec) := 1'''
    )


def write_raw(raw_path, img_np):
  """
  Write raw data from a numpy array to a binary file.
  """
  img_np.flatten('F').astype('float32').tofile(raw_path)


def parse_args():
  """
  Parse arguments for function_to_image.
  """
  parser = argparse.ArgumentParser()
  parser.add_argument('--output', '-o', help="output prefix", required=True)
  parser.add_argument(
      '--function',
      '-f',
      help="image function",
      required=True,
      choices=FUNCTIONS.keys()
  )
  return parser.parse_args()


if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  args = parse_args()
  function_to_image(args.output, args.function)
