"""Utilities around opening and processing netcdfs from this project."""
import numpy as np
import pathlib
from typing import Union
import xarray as xr


def fix_calendar(
    xr_in: Union[xr.Dataset, xr.DataArray], timevar: str = "T"
) -> Union[xr.Dataset, xr.DataArray]:
    """Fix and decode the calendar.

    Args:
        xr_in (Union[xr.Dataset, xr.DataArray]): the xarray object input
        timevar (str, optional): The time variable name. Defaults to "T".

    Returns:
        Union[xr.Dataset, xr.DataArray]: same type and xr_in with fixed calendar.

    """
    # make all into dataset
    if isinstance(xr_in, xr.DataArray):
        ds = xr_in.to_dataset()
    else:
        ds = xr_in

    t_list = ["T_0" + str(x) for x in range(5)]
    t_list.append("T")
    t_list.append("time")
    t_list.append(timevar)

    for t_dim in t_list:

        if t_dim in ds.dims:
            # add 360_day attribute
            if "calendar" not in ds[t_dim].attrs:
                ds[t_dim].attrs["calendar"] = "360_day"
            else:
                if ds[t_dim].attrs["calendar"] == "360":
                    ds[t_dim].attrs["calendar"] = "360_day"

    # decode
    ds = xr.decode_cf(ds)

    # transform back into original type
    if isinstance(xr_in, xr.DataArray):
        xr_out = ds.to_array()
    else:
        xr_out = ds

    return xr_out


def om_rdict(index: int) -> dict:
    """Returns renaming dict for xarray.DataArray output of ocean model.

    Made to reformat the output datarrays of the Fortran
    ocean model used.

    Args:
        index (int): index on coords.

    Returns:
        dict: renaming dict.

    """
    return {
        "T_0" + str(index): "T",  # "time",
        "Y_0" + str(index): "Y",  # "y",
        "X_0" + str(index): "X",  # "x",
        "L_0" + str(index): "Z",  # "Z",
    }


def can_coords(
    xr_obj: Union[xr.Dataset, xr.DataArray]
) -> Union[xr.Dataset, xr.DataArray]:
    """
    Transform an object into having the canonical coordinates if possible.

    Fail hard if impossible.

    TODO: Should fail hard at the moment, need to setup.

    Args:
        xr_obj (Union[xr.Dataset, xr.DataArray]): The dataset or datarray to
            canonicalise.

    Returns:
        Union[xr.Dataset, xr.DataArray]: The dataset that has been canoncilised.
            Function will raise an assertion error otherwise.
    """
    assert isinstance(xr_obj, Union[xr.DataArray, xr.Dataset])

    assert 1 < 2

    return xr_obj


def sel(
    xr_obj: Union[xr.Dataset, xr.DataArray], reg="pac"
) -> Union[xr.Dataset, xr.DataArray]:
    """
    Select a region of the dataset or datarray.

    Assumes
    reg options: "pac', 'nino3.4', "glob"
    https://www.ncdc.noaa.gov/teleconnections/enso/indicators/sst/

    Args:
        xr_obj (Union[xr.Dataset, xr.DataArray]): The xarray object.
            Needs to have canonical coordinates.
        reg (str, optional): The keyword region to select. Defaults to 'pac'.

    Returns:
        Union[xr.Dataset, xr.DataArray]: The downsized xarray object.

    Example:
        Effect example::

                if reg == "pac":
                    return xr_obj.sel(X=slice(100, 290), Y=slice(-30, 30))
                elif reg == "nino3.4":
                    return xr_obj.sel(X=slice(190, 240), Y=slice(-5, 5))
                elif reg == "nino4":
                    return xr_obj.sel(X=slice(160, 210), Y=slice(-5, 5))
                elif reg == "nino3":
                    return xr_obj.sel(X=slice(210, 270), Y=slice(-5, 5))
                elif reg == "nino1+2":
                    return xr_obj.sel(X=slice(270, 280), Y=slice(-10, 0))

    """

    sel_d = {
        "pac": {"X": (100, 290), "Y": (-30, 30)},
        "nino1+2": {"X": (270, 280), "Y": (-10, 0)},
        "nino3": {"X": (210, 270), "Y": (-5, 5)},
        "nino3.4": {"X": (190, 240), "Y": (-5, 5)},
        "nino4": {"X": (160, 210), "Y": (-5, 5)},
    }

    assert reg in sel_d

    sel_c = sel_d[reg]

    return xr_obj.sel(
        X=slice(sel_c["X"][0], sel_c["X"][1]), Y=slice(sel_c["Y"][0], sel_c["Y"][1])
    )


def open_dataset(path: Union[str, pathlib.Path]) -> xr.Dataset:
    """
    Open a dataset and formats it.

    Args:
        path (Union[str, pathlib.Path]): the path to the netcdf dataset file.

    Returns:
        xr.Dataset: The formatted dataset.
    """
    return fix_calendar(xr.open_dataset(str(path), decode_times=False))


def open_dataarray(path: Union[str, pathlib.Path]) -> xr.DataArray:
    """
    Open a dataarray and format it.

    Args:
        path (Union[str, pathlib.Path]): the path to the netcdf datarray file.

    Returns:
        xr.DataArray: The formatted datarray.
    """
    return fix_calendar(xr.open_dataarray(str(path), decode_times=False))


def cut_and_taper(
    da: xr.DataArray,
    y_var: str = "Y",
    x_var: str = "X",
) -> xr.DataArray:
    """
    Cut and taper a field by latitude.

    Since the atmosphere model dynamics are only applicable
    in the tropics, the computed wind stress anomaly is only
    applied to the ocean model between 20° S and 20° N, and
    is linearly tapered to zero at 25° S and 25° N.

    Currently only copes if the array is two dimensional.

    Args:
        da (xr.DataArray): The datarray.
        y_var (str, optional): The name of the Y coordinate. Defaults to "Y".
        x_var (str, optional): The name of the X coordinate. Defaults to "X".

    Returns:
        xr.DataArray: The datarray with the function applied.

    Example:
        Should achieve::

            if da.Y > 25 or da.Y < -25:
                da = 0.0
            elif 20 <= da.Y <= 25:
                da = da - (0.2* (da.Y- 20))) * da
            else -20 >= da.Y >= -25:
                da = da - (0.2* (-da.Y - 20)) * da

        Usage::

            from src.xr_utils import open_dataset, cut_and_taper
            from src.constants import OCEAN_DATA_PATH
            da_new: xr.DataArray = open_dataset(OCEAN_DATA_PATH / "qflx.nc").qflx
            cut_and_taper(da_new.isel(Z=0, T=0, variable=0))

    """
    # make sure that they are in the correct order.
    da = da.transpose(y_var, x_var)

    @np.vectorize
    def test_vec(x: float, y: float):
        if y > 25 or y < -25:
            x = 0.0
        elif 20 <= y <= 25:
            x = x - (0.2 * (y - 20)) * x
        elif -20 >= y >= -25:
            x = x - (0.2 * (-y - 20)) * x
        return x

    for x in range(len(da.coords[x_var].values)):
        da[:, x] = test_vec(da[:, x], da.coords[y_var])

    return da
