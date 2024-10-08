"""Resize an Interfile image by cropping and padding.

This script resizes an Interfile image so that another region of the space is covered.
It DOES NOT modify, stretch or interpolate any data in any way; instead, it just crops the image
where needed and pad it with empty values (0) where needed.

In some use cases, it can be useful to also flip the data, which can be achieved using the
--x-flip, --y-flip and --z-flip flags. Flipping is done after resizing was performed.

Everything is expressed in voxels and not in millimeters.

Although the script operates in 3D, here is an example in 2D:

    +---------------+
    |        NEW    |
  +-|---+   IMAGE   |
  | +---------------+
  | OLD |
  |IMAGE|
  +-----+

  In this example, OLD IMAGE is a 7×5 image, and we want it to cover the region covered by NEW
  IMAGE (17×4), which is shifted from OLD IMAGE by 2 pixels in the x direction and 1 pixel in the y
  direction.
  This can be achieved by running the following (pseudo-)command:

    python -m image_tools.resize_image \
      -i OLD_IMAGE.hdr \
      -o NEW_IMAGE \
      --x-size 17 \
      --y-size 4 \
      --x-shift 2 \
      --y-shift 1

  The following will happen:
    - Pixel data within OLD IMAGE and outside of NEW IMAGE will be discarded (cropping);
    - Pixel data within NEW IMAGE and outside of OLD IMAGE will be set to 0 (padding);
    - Pixel data located at the intersection between OLD IMAGE and NEW IMAGE will be copied to NEW
      IMAGE and properly placed in the matrix.

  If OLD IMAGE and NEW IMAGE happen to be disjoint, then NEW IMAGE would be completely filled with
  zeroes.
"""

import argparse
import logging

import numpy as np
from pet_imaging_tools.image_processing.image_tools import (
    get_info_from_interfile_header, transform_interfile_header
)


def get_output_matrix_size(input_matrix_size, desired_size):
  """
  Get the size of the output matrix, based on the desired size and the size of the input matrix.
  """
  output_matrix_size = tuple(
      input_matrix_size[i] if desired_size[i] is None else desired_size[i]
      for i in range(3)
  )
  logging.debug("Output matrix size: %s", output_matrix_size)
  return output_matrix_size


def get_shifts(input_shifts):
  """
  Get the shifts, with a default value of 0 if no shift was provided in a dimension.
  """
  shifts = tuple(
      0 if input_shifts[i] is None else input_shifts[i] for i in range(3)
  )
  logging.debug("Shifts to be used: %s", shifts)
  return shifts


def get_slices(shift, input_axis_size, output_axis_size):
  """
  Compute the array slices necessary to determine which data to copy from the input matrix to the
  output one.
  """
  border_input_low, border_input_high = -(
      input_axis_size // 2
  ), input_axis_size // 2 + input_axis_size % 2
  border_output_low, border_output_high = shift - (
      output_axis_size // 2
  ), shift + output_axis_size // 2 + output_axis_size % 2
  logging.debug("Shift: %s", shift)
  logging.debug(
      "Input size: %s, borders: %s", input_axis_size,
      (border_input_low, border_input_high)
  )
  logging.debug(
      "Output size: %s, borders: %s", output_axis_size,
      (border_output_low, border_output_high)
  )

  if border_input_low > border_output_high or border_input_high < border_output_low:
    # Disjoint case
    slice_input_low = slice_output_low = slice_input_high = slice_output_high = 0
  else:
    if border_input_low < border_output_low:
      slice_input_low = border_output_low - border_input_low
      slice_output_low = 0
    else:
      slice_input_low = 0
      slice_output_low = border_input_low - border_output_low
    if border_input_high < border_output_high:
      slice_input_high = input_axis_size
      slice_output_high = output_axis_size - (
          border_output_high - border_input_high
      )
    else:
      slice_input_high = input_axis_size - (
          border_input_high - border_output_high
      )
      slice_output_high = output_axis_size

  slice_input = slice(slice_input_low, slice_input_high)
  slice_output = slice(slice_output_low, slice_output_high)

  return slice_input, slice_output


def resize_image(input_image_np, output_matrix_size, shifts):
  """
  Resize the input image by copying the overlap region with the output image. No interpolation is
  performed, data is truncated where needed, and padded with zeroes where needed.
  """

  slices_input = [slice(None, None, None) for _ in range(3)]
  slices_output = [slice(None, None, None) for _ in range(3)]

  for axis in range(3):

    logging.debug("Processing axis %s", axis)

    shift = shifts[axis]
    input_axis_size = input_image_np.shape[axis]
    output_axis_size = output_matrix_size[axis]

    slice_input, slice_output = get_slices(
        shift, input_axis_size, output_axis_size
    )

    logging.debug("Slice input: %s", slice_input)
    logging.debug("Slice output: %s", slice_output)

    slices_input[axis] = slice_input
    slices_output[axis] = slice_output

  output_image_np = np.zeros(output_matrix_size)
  output_image_np[tuple(slices_output)] = input_image_np[tuple(slices_input)]

  return output_image_np


def flip_image(image_np, flips):
  """
  Flip the image in the determined axes.
  """
  flip_axis = tuple(i for i in range(len(flips)) if flips[i])
  return np.flip(image_np, flip_axis)


def save_output_header(input_header, output, output_matrix_size):
  """
  Generate the header of the output image.
  """
  output_header = output + '.hdr'
  transform_list = [
      ('!name of data file', output + '.img'),
      ('!matrix size [1]', str(output_matrix_size[0])),
      ('!matrix size [2]', str(output_matrix_size[1])),
      ('!matrix size [3]', str(output_matrix_size[2]))
  ]
  transform_interfile_header(input_header, output_header, transform_list)


def save_output_image(output_image_np, output, dtype):
  """
  Save the binary data of the output image.
  """
  output_image_np.flatten('F').astype(dtype).tofile(output + '.img')


def parse_args():
  """
  Parse arguments to resize image.
  """
  parser = argparse.ArgumentParser(
      description="resize an image by cropping and padding"
  )
  parser.add_argument(
      '-i', '--input-header', help="Interfile header path", required=True
  )
  sizes = parser.add_argument_group("new dimensions")
  shifts = parser.add_argument_group("dimension shifts")
  flips = parser.add_argument_group("dimension flips")
  for dim in ['x', 'y', 'z']:
    sizes.add_argument(f'--{dim}-size', help=f"new {dim} size", type=int)
    shifts.add_argument(
        f'--{dim}-shift',
        help=f"shift in {dim} dimension to crop/pad",
        type=int
    )
    flips.add_argument(
        f'--{dim}-flip',
        help=f"flip output in {dim} dimension",
        default=False,
        action='store_true'
    )
  parser.add_argument(
      '-o',
      '--output',
      help="output base path (without extension)",
      required=True
  )
  parser.add_argument(
      '--debug', help="debug mode", default=False, action='store_true'
  )
  return parser.parse_args()


def main():
  """
  Parse input arguments and resize images.
  """

  args = parse_args()

  logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

  input_sizes = (args.x_size, args.y_size, args.z_size)
  input_shifts = (args.x_shift, args.y_shift, args.z_shift)
  input_flips = (args.x_flip, args.y_flip, args.z_flip)

  input_image, _, input_matrix_size, dtype = get_info_from_interfile_header(
      args.input_header
  )
  logging.debug("Input header has size %s, dtype %s", input_matrix_size, dtype)

  output_matrix_size = get_output_matrix_size(input_matrix_size, input_sizes)
  shifts = get_shifts(input_shifts)

  input_image_np = np.fromfile(
      input_image, dtype=dtype
  ).reshape(
      input_matrix_size, order='F'
  )

  output_image_np = resize_image(input_image_np, output_matrix_size, shifts)

  output_image_flipped_np = flip_image(output_image_np, input_flips)

  save_output_header(args.input_header, args.output, output_matrix_size)
  save_output_image(output_image_flipped_np, args.output, dtype)


if __name__ == '__main__':
  main()
