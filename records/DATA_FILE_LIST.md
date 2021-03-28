
## Data structure

 - Are the files with the same names in different places identical?
 - If so, why is there so much duplication of data?

```
atmos-model
  DATA/      # everything ending with clim60 read by dQ.py
    ps-ECMWF-clim.nc          # read in by TCAM.py
    ts-ECMWF-clim60.nc        # read in by dQ.py
    sfcWind-ECMWF-clim60.nc   # read in by dQ.py
    pr-ECMWF-trend.nc         # read in by TCAM.py 
    sst-ECMWF-clim.nc         # read in by TCAM.py
    mask-360x181.nc
    ts-ECMWF-clim.nc          # read in by TCAM.py
    mask-360x180.nc          
    clt-ECMWF-clim60.nc       # read in by dQ.py
    ts-ECMWF-trend.nc         # read in by TCAM.py
    sst-ECMWF-trend.nc        # read in by TCAM.py
    rh-fixed-clim60.nc        # read in by dQ.py
    rh-ECMWF-clim60.nc        # read in by dQ.py
    sfcWind-ECMWF-clim.nc     # read in by TCAM.py
    pr-ECMWF-clim.nc          # read in by TCAM.py
  tmp/
    S91-Hq1800-PrcpLand1.nc
    S91-Hq1800-PrcpLand0.nc
ocean-model
  RUN
    output
      om_spin.20y.restart
      om_run2f.nc           # Full time period videos made (>624 frames) and put on youtube.
      om_spin.nc
      om_spin.save
      om_run2f.save
      om_diag.2y.restart
      om_diag.nc
      om_diag.save
      om_diag.data
      om_diag.indx
    DATA
      rzk.pro
      spline_ECMWF.txt
      dQdf-sample.nc
      om_mask.nc
      qflx.nc
      tau-ECMWF.y
      sst-ECMWF-clim.nc
      tau-ECMWF.x
      dQdT-sample.nc
      qflx-0.nc
      tau-ECMWF-clim.x
      tau-ECMWF-clim.y
    om_diag.tr
  DATA
    rzk.pro
    spline_ECMWF.txt
    dQdf-sample.nc
    om_mask.nc
    qflx.nc
    tau-ECMWF.y
    sst-ECMWF-clim.nc
    tau-ECMWF.x
    dQdT-sample.nc
    qflx-0.nc
    tau-ECMWF-clim.x
    tau-ECMWF-clim.y
  SRC
    output
      om_spin.20y.restart
      om_diag.nc
      om_test.indx
      om_diag.save
      om_diag.data
      om_test.data
      om_test.save
      om_diag.indx
    DATA
      rzk.pro
      spline_ECMWF.txt
      dQdf-sample.nc
      om_mask.nc
      qflx.nc
      tau-ECMWF.y
      sst-ECMWF-clim.nc
      tau-ECMWF.x
      dQdT-sample.nc
      qflx-0.nc
      tau-ECMWF-clim.x
      tau-ECMWF-clim.y
```

## Code structure:

 - Duplication of code between `jupyter-notebook` and the `python` script.

```
ocean-model
  TCAM.ipynb
  TCAM.py
  dQ.py
  dQ.ipynb
  DATA/
  tmp/
atmos-model
  RUN
    run-model
    diag.tios
    om_diag.log
    om_run2f
    qflx.ing
    output/
    month.tios
    spin.tios
    om_diag
    om_spin
    DATA/
  DATA/
  SRC
    om_mem.F
    wrap-mod.F
    om_data.h
    diag.tios
    om_test.tr
    om_diag.log
    om_qflux.F
    om_forc.F
    om_leap.F
    Makefile
    sst-mod.F
    netcdf.inc
    qflx.ing
    output/
    cuf.h
    om_main.F
    om_core.F
    om_core.h
    om_sst.h
    README
    om_sst.F
    sio.c
    om_equi.h
    om_equi.F
    codb.c
    om_tios.F
    om_wrap.h
    tios2cdf.c
    om_wrap.F
    om_test
    om_ekm.F
    om_c.c
    fodb.F
    om_diag
    data-mod.F
    om_para.h
    DATA/
    tios.h
    om_diag.tr
    daio.c
    om_test.log
```
