""" Sets of helper functions used by some tests
"""

import os
import requests


def download_file(
    filename,
    out_folder,
    url='http://sphinx.if.uj.edu.pl/test_data/total-body-tools/'
):
  """
  Download a file to be used for testing purposes.
  """
  url = url + filename
  result = requests.get(url)
  with open(os.path.join(out_folder, filename), 'wb') as out_file:
    out_file.write(result.content)
