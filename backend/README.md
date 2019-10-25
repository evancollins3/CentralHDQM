# HDQM backend

there has to be a file named `connection_string.txt` in this directory containing a database connection string in the first line. This is required for Extractor and API parts to function.

## Extractor
Extracts the monitor elements from DQM files in eos and performs HDQM based on configuration files in `extractor/cfg/subsystem/*.ini` 

## API
REST API serving JSON data to a frontend.
