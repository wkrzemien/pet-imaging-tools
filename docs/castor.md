# CASToR datafiles

## CASToR

CASToR (Customizable and Advanced Software for Tomographic Reconstruction) is a C++ software for tomographic image reconstruction widely used for research purposes. According to [its website](https://www.castor-project.org/),
> CASToR is an open-source multi-platform project for 4D emission (PET and SPECT) and transmission (CT) tomographic reconstruction.

## CASToR datafiles

Once again quoting [the website](https://www.castor-project.org/),
> A generic and flexible input data file format has been designed in order to integrate all the information needed for the reconstruction, for any modality and for any data format (list-mode or histogram).

A CASToR datafile consists of two files:

- a header datafile (*.Cdh), which is a key-value text file that gives general information about the datafile, such as which kind of data it contains
- a binary datafile (*.Cdf), which contains a series of raw floating point or integer data. Interpretation of these data is defined by the content of the header.

Additional information about the datafile format can be found in [CASToR official documentation](https://castor-project.org/sites/default/files/2020-09/CASToR_general_documentation.pdf), more specifically in section 6.

## Interacting with CASToR datafiles

By default, CASToR is not distributed with any tools that allows to easily manipulate those datafiles. By "manipulating datafiles", we mean:

- means of adding additional data columns (to incorporate additional information such as normalization coefficients or scatter or random corrections)
- means of deleting data columns
- means of updating data columns
- means of editing the header in a way which is reflected in the datafile.

The module `pet_imaging_tools.castor_datafile` aims at providing a toolbox to perform basic operations on those datafiles. This module was designed with datafiles for CASToR 3.1.1 in mind. Only PET list-mode data is currently implemented, but the code can be extended to accomodate for other kinds of data, such as histogram, SPECT or CT datafiles.
Please refer to [the reference](reference.md#pet_imaging_tools.castor_datafile) for additional details about this module.
