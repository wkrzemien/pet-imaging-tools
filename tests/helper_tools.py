""" Sets of helper functions used by some tests
"""

import requests


def download_file(
    filename,
    out_folder,
    url='http://sphinx.if.uj.edu.pl/test_data/total-body-tools/'
):
  url = url + filename
  result = requests.get(url)
  with open(out_folder + filename, 'wb') as out_file:
    out_file.write(result.content)
