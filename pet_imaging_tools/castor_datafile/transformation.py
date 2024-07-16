#!/usr/bin/env python3
"""Transform CASToR datafiles (*.Cdh and *.Cdf).

So far only PET list-mode data is supported.

(Simplified) PET list-mode format
  Symbol  Description Type  Mandatory
1 t Time in ms  uint32_t  yes
2 a Attenuation correction factor FLTNBDATA no
3 s Un-normalized scatter intensity rate  FLTNBDATA no
4 r Un-normalized random intensity rate FLTNBDATA no
5 n Normalization factor of the corresponding event FLTNBDATA no
6 TOF Difference in arrival time between c1 and c2  FLTNBDATA no
7 k Number of contributing crystal pairs  uint16_t  no
8.1 c1  Crystal ID 1  uint32_t  yes
8.2 c2  Crystal ID 2  unint32_t yes
(source: https://castor-project.org/sites/default/files/2020-09/CASToR_general_documentation.pdf)
"""

import re
import sys
import os
import logging
from strenum import StrEnum

import tqdm

import numpy as np
import dask.dataframe as dd


class CASToRCDHKey(StrEnum):
  """CASToR CDH keys."""
  DATA_FILENAME = 'Data filename'
  NUMBER_OF_EVENTS = 'Number of events'
  ATTENUATION_CORRECTION_FLAG = 'Attenuation correction flag'
  SCATTER_CORRECTION_FLAG = 'Scatter correction flag'
  RANDOM_CORRECTION_FLAG = 'Random correction flag'
  NORMALIZATION_CORRECTION_FLAG = 'Normalization correction flag'
  TOF_INFORMATION_FLAG = 'TOF information flag'


class CASToRCDFField(StrEnum):
  """CASToR CDF fields."""
  TIMESTAMP = 't'
  ATTENUATION = 'a'
  SCATTER = 's'
  RANDOM = 'r'
  NORMALIZATION = 'n'
  TOF = 'TOF'
  CRYSTAL_ID_1 = 'c1'
  CRYSTAL_ID_2 = 'c2'


# Column types
UINT32_T = '<i4'
FLTNBDATA = '<f4'


class CASToRCDFType(StrEnum):
  """Types associated to a given CASToR CDF field."""
  TIMESTAMP = UINT32_T
  ATTENUATION = FLTNBDATA
  SCATTER = FLTNBDATA
  RANDOM = FLTNBDATA
  NORMALIZATION = FLTNBDATA
  TOF = FLTNBDATA
  CRYSTAL_ID = UINT32_T


# Mapping from flag to columns
FLAGS = {
    CASToRCDHKey.ATTENUATION_CORRECTION_FLAG:
        {
            'column': CASToRCDFField.ATTENUATION,
            'type': CASToRCDFType.ATTENUATION
        },
    CASToRCDHKey.SCATTER_CORRECTION_FLAG:
        {
            'column': CASToRCDFField.SCATTER,
            'type': CASToRCDFType.SCATTER
        },
    CASToRCDHKey.RANDOM_CORRECTION_FLAG:
        {
            'column': CASToRCDFField.RANDOM,
            'type': CASToRCDFType.RANDOM
        },
    CASToRCDHKey.NORMALIZATION_CORRECTION_FLAG:
        {
            'column': CASToRCDFField.NORMALIZATION,
            'type': CASToRCDFType.NORMALIZATION
        },
    CASToRCDHKey.TOF_INFORMATION_FLAG:
        {
            'column': CASToRCDFField.TOF,
            'type': CASToRCDFType.TOF
        }
}


class StopProcessingException(Exception):
  """
  The following class is used in Cdf-updating callbacks to tell the script that processing should
  stop.
  This is useful if no additional rows will be written to the file, for instance when truncating a
  file.
  """


def read_cdh_field(cdh_content, field):
  """Read a field from a CASToR data header file.

  Args:
    cdh_content (str): content of the CASToR data header file.
    field (str): field to read.

  Returns:
    Value of the field, or None if the field is not found. Raises a ValueError is the field is
    found more than once.
  """
  field_matches = re.findall(
      rf'^{field}\s*:\s*(\S+)\s*$', cdh_content, re.MULTILINE
  )
  number_of_matches = len(field_matches)

  if number_of_matches == 0:
    return None

  if number_of_matches > 1:
    raise ValueError(f"{field} found {number_of_matches} times, aborting.")

  return field_matches[0]


def replace_cdh_field(cdh_content, field, new_value):
  """Replace a field in a CASToR data header file. If the field is not found, nothing happens.

  Args:
    cdh_content (str): content of the CASToR data header file.
    field (str): field whose content to replace.
    new_value (str): new value for the field.
  """
  return re.sub(
      f'^{field}.+$', f'{field}: {new_value}', cdh_content, flags=re.MULTILINE
  )


def is_list_mode(cdh_content):
  """Check if a CASToR data header file represents list-mode data.

  Args:
    cdh_content (str): content of the CASToR data header file.

  Returns:
    Boolean indicating whether the file represents list-mode data.
  """
  data_mode = read_cdh_field(cdh_content, 'Data mode')
  if data_mode is None:
    raise ValueError(
        "Data mode, a mandatory field, is missing from CASToR data header."
    )
  return data_mode == 'list-mode'


def check_flag(cdh_content, flag):
  """Check if some flag was set in a CASToR data header file.

  Args:
    cdh_content (str): content of the CASToR data header file.
    flag (str): flag to check.

  Returns:
    Boolean indicating whether the flag is set.
  """
  flag = read_cdh_field(cdh_content, flag)
  if flag is None:
    return False
  return bool(int(flag))


def get_flags(cdh_content):
  """Get flags from a CASToR data header file.

  Args:
    cdh_content (str): content of the CASToR data header file.

  Returns:
    Dictionnary that maps to each flag a boolean indicating whether the flag is enabled.
  """

  flags = {}

  for flag, _ in FLAGS.items():
    flags[flag] = check_flag(cdh_content, flag)

  return flags


def max_nb_of_lines_per_event(cdh_content):
  """Get the maximum number of lines per event as defined in the content of a CASToR data header
  file.

  Args:
    cdh_content (str): content of the CASToR data header file.

  Returns:
    Maximum number of lines per event.
  """
  mnolpe = read_cdh_field(cdh_content, "Maximum number of lines per event")
  if mnolpe is None:
    return 1
  return int(mnolpe)


def get_cdf_path(cdh_content, cdh_filename):
  """Get the path of the CASToR data file pointed by the CASToR data header.

  Note: this function assumes that the path of the CASToR data file is given relatively to that of
  the CASToR header file.

  Args:
    cdh_content (str): content of the CASToR data header file.
    cdh_filename (str): file name of the CASToR data header.

  Returns:
    Path of the CASToR data file.
  """
  cdf_filename = read_cdh_field(cdh_content, CASToRCDHKey.DATA_FILENAME)
  cdh_dirname = os.path.dirname(cdh_filename)
  return os.path.join(cdh_dirname, cdf_filename)


def get_dtype(flags):
  """Get data types corresponding to a dictionnary of flags.

  Args:
    flags (dict): dictionnary that maps each flag to a boolean.

  Returns:
    Data types corresponding to the array of flags.
  """
  dtype_array = [(CASToRCDFField.TIMESTAMP, CASToRCDFType.TIMESTAMP)]

  for flag, enabled in flags.items():
    if enabled:
      column = FLAGS[flag]['column']
      flag_type = FLAGS[flag]['type']
      dtype_array.append((column, flag_type))

  dtype_array.append((CASToRCDFField.CRYSTAL_ID_1, CASToRCDFType.CRYSTAL_ID))
  dtype_array.append((CASToRCDFField.CRYSTAL_ID_2, CASToRCDFType.CRYSTAL_ID))

  return np.dtype(dtype_array)


def write_row(row, output_cdf_file):
  """Write a row to a Cdf file.

  Args:
    row (dict): the row to write.
    output_cdf_file (TextIOWrapper): the file in which the row will be written.
  """
  output_cdf_file.write(
      np.dtype(CASToRCDFType.TIMESTAMP).type(row[CASToRCDFField.TIMESTAMP])
  )

  for flag in FLAGS.values():
    column = flag['column']
    if column in row.keys():
      flag_type = flag['type']
      output_cdf_file.write(np.dtype(flag_type).type(row[column]))

  output_cdf_file.write(
      np.dtype(CASToRCDFType.CRYSTAL_ID
               ).type(row[CASToRCDFField.CRYSTAL_ID_1])
  )
  output_cdf_file.write(
      np.dtype(CASToRCDFType.CRYSTAL_ID
               ).type(row[CASToRCDFField.CRYSTAL_ID_2])
  )


def write_new_cdh_file(
    output_cdh, cdf_filename, cdh_content, update_cdh=lambda cdh: cdh
):
  """Write new CASToR header file.

  Args:
    output_cdh (str): output CASToR header file.
    output_cdf (str): output CASToR data file.
    cdf_filename (str): name of the cdf file to be written in the new header.
    update_cdh (str -> str): function that updates the Cdh file. Defaults to identity function.
  """
  with open(output_cdh, 'w', encoding='utf-8') as output_cdh_file:
    cdh_with_updated_cdf = replace_cdh_field(
        cdh_content, CASToRCDHKey.DATA_FILENAME, cdf_filename
    )
    output_cdh_file.write(update_cdh(cdh_with_updated_cdf))
  logging.info("Successfully wrote %s.", output_cdh)


def write_new_cdf_file(output_cdf, cdf_dd, update_row=lambda row: row):
  """Write new CASToR header file.

  Args:
    output_cdf (str): output CASToR data file.
    cdf_dd(): .
    update_row (dict -> dict): function that updates a row. Defaults to identity function.
  """
  with open(output_cdf, 'w+b') as output_cdf_file, tqdm.tqdm(
      total=cdf_dd.shape[0].compute()) as progress:
    try:
      for row in cdf_dd.itertuples():
        new_row = update_row(row._asdict())
        if new_row is not None:
          write_row(new_row, output_cdf_file)
        progress.update(1)
    except StopProcessingException:
      pass

  logging.info("Successfully wrote %s.", output_cdf)


def get_dd_from_cdf_file(cdf_path, cdf_dt, chunksize):
  """Reads a content (image) of the CASToR data file and
     transform it into a dask array.

  Args:
    cdf_path (str): the CASToR data file.
    cdf_dt (numpy.dtype): numpy data type object describing types of object to be stored in the
                          array
    chunksize (int): size of chunks used in the dask.dataframe.from_array() function.
  """
  with open(cdf_path, 'rb') as cdf_file:
    cdf_dd = dd.from_array(
        np.frombuffer(cdf_file.read(), cdf_dt), chunksize=chunksize
    )
    logging.info("Successfully read %s.", cdf_path)
  return cdf_dd


def get_cdf_and_cdh_content_from_file(cdh_path, chunksize=int(1e7)):
  """Returns the content of the CASToR header file
     and the CASTOR datafile. The CASTOR datafile
     is given in dask.dataframe format

  Args:
    cdh_path (str): the CASToR header file.
    chunksize (int): size of chunks used in
                     the dask.dataframe.from_array() function.
  """
  with open(cdh_path, 'r+', encoding='utf-8') as cdh_file:
    cdh_content = cdh_file.read()

    if not is_list_mode(cdh_content):
      sys.exit("Only list-mode data is supported.")

    if max_nb_of_lines_per_event(cdh_content) > 1:
      sys.exit("Only a maximum number of lines per event of 1 is supported.")

    flags = get_flags(cdh_content)
    cdf_dt = get_dtype(flags)

    cdf_path = get_cdf_path(cdh_content, cdh_path)

    logging.info("Successfully read %s.", cdh_path)

    cdf_dd = get_dd_from_cdf_file(cdf_path, cdf_dt, chunksize=chunksize)
  return cdh_content, cdf_dd


def update_castor_datafile(
    cdh_path,
    output_cdh,
    output_cdf,
    update_cdh=lambda cdh: cdh,
    update_row=lambda row: row,
):
  """Update a pair of CASToR header/data file.

  Args:
    cdh_path (str): the CASToR header file.
    output_cdh (str): output CASToR header file.
    output_cdf (str): output CASToR data file.
    update_cdh (str -> str): function that updates the Cdh file. Defaults to identity function.
    update_row (dict -> dict): function that updates a row. Defaults to identity function.
  """
  try:
    cdh_content, cdf_dd = get_cdf_and_cdh_content_from_file(cdh_path)
    cdf_filename = os.path.split(output_cdf)[1]
    write_new_cdh_file(output_cdh, cdf_filename, cdh_content, update_cdh)
    write_new_cdf_file(output_cdf, cdf_dd, update_row)

  except FileNotFoundError as file_not_found:
    logging.error("File not found: %s.", file_not_found.filename)
    sys.exit(1)
