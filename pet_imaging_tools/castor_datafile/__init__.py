"""
This module defines a set of functions to programmatically interact with CASToR datafiles, both on
the data contained in the header (*.Cdh), but also on the binary data defined in the datafile
itself.

This module also defines a set of operations designed to be used directly from the command line.
These operations rely on a single entry point, the function update_castor_datafile. This function
can be used to easily define additional tools. It works through two callbacks: one that defines how
the header must be transformed, and the second that defines how each row must be transformed.
Examples of how this function can be used can be found in the source code of the command-line tools.
"""

from pet_imaging_tools.castor_datafile.transformation import *
