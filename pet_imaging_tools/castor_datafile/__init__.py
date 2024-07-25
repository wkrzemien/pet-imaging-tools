"""
This module defines a set of functions to programmatically interact with CASToR datafiles, both on
the metadata contained in the header (*.Cdh), but also on the binary data defined in the CASTOR
datafile itself.

This module also defines a set of operations designed to be used directly from the command line.
These operations allow to easily edit CASToR datafiles, for instance by:
- allowing to add normalization factors to a CASToR datafile
- truncating a CASToR datafile, to keep only a subset of events
- replicating a CASToR datafile, while performing sampling with repetition on its list of events
One can create additional tools using the set of building blocks that allow to parse CASToR
datafile headers, load its data into memory, and write edited data to the disk.

These operations rely on a single entry point, the function update_castor_datafile. This function
can be used to easily define additional tools. It works through two callbacks: one that defines how
the header must be transformed, and the second that defines how each row must be transformed.
Examples of how this function can be used can be found in the source code of the command-line tools.
"""

from pet_imaging_tools.castor_datafile.transformation import *
