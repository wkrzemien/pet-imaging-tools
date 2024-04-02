"""Utils functions for transform_castor_datafile."""

import argparse


def default_parser(desc):
  """Base argument parser that reads inputs and outputs."""
  parser = argparse.ArgumentParser(description=desc)
  parser.add_argument('--cdh', help="CASToR data header", required=True)
  # In the future: change to single output
  parser.add_argument('--output-cdf', help="output Cdf file", required=True)
  parser.add_argument('--output-cdh', help="output Cdh file", required=True)
  return parser
