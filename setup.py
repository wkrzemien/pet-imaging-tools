"""Package definition for pet-imaging-tools."""
from setuptools import setup, find_packages

setup(
    name='pet-imaging-tools',
    version='0.0.1',
    description='Collection of useful tools and scripts for PET imaging',
    url='https://github.com/JPETTomography/pet-imaging-tools',
    author='Aurélien Coussat et al.',
    license_files=('LICENSE', ),
    packages=find_packages(),
    install_requires=['dask[dataframe]', 'numpy', 'pandas', 'tqdm', 'StrEnum', 'gatetools'],
    scripts=[
        'pet_imaging_tools/castor_datafile/add_normalization_factors.py',
        'pet_imaging_tools/castor_datafile/replicate.py',
        'pet_imaging_tools/castor_datafile/truncate.py'
    ]
)
