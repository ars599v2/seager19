# Data loading

```txt
data_loading
|
├── __init__.py    <- Makes src a Python module
|
├── download.py   <- Get the data from dropbox through various functions.
|
├── get_cmip6     <- Make the cmip6 ensembles for surface variables (will only work on Pangeo).
|
├── ingrid.py    <- The ingrid replacement for the middle part of the ocean model.
|
├── make_cmip5.py   <- Get the CMIP5 and CMIP6 data and process it for the atmosphere model.
|
└── move_old.py    <- Move an old folder and delete it.
```