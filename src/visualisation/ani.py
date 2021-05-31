"""ani.py - A set of functions to animate particular results.

animate_xr_da - animation for individual xr.DataArray.

animate_prediction - plots inputs and outputs of old model.

"""
import os
from typing import Callable, Optional
import numpy as np
import xarray as xr
from tqdm import tqdm
import matplotlib
import matplotlib.pyplot as plt
import imageio
from src.plot_settings import ps_defaults, time_title, cmap  # ,label_subplots
from src.utils import timeit, fix_calendar
from src.data_loading.transforms import rdict


@timeit
def animate_ds(
    ds: xr.Dataset,
    file_name: str,
    output_dir: str,
    dpi: float = 200,
    front_trim: int = 0,
    plot_list: Optional[list] = None,
) -> None:
    """Animate the `xarray.Dataset`.

    Args:
        ds (xr.Dataset): xarray.Dataset to animate the variables of.
        file_name (str): Name of dataset to be associated with the animations.
        output_dir (str): Full path to output directory to put the animations in.
        dpi (float): the dots per inch for the figure. Defaults to 200.
        front_trim (int): the number of time indices to remove from the front of the
            xr.DataArray pieces. Defaults to 0.
        plot_list (Optional[list], optional): Subset of variables to plot. Defaults
            to None. Introduced so that I could speed up the test animation,
            while still covering the function.
    """
    ps_defaults(use_tex=False, dpi=dpi)
    cmap_d = {
        "DYN_PRES": "delta",
        "SST_QFLX": "delta",
        "SST_SST": "sst",
        "qflx": "delta",
        "QFLX": "delta",
        "TDEEP_HTHERM": "sst",
        "TDEEP_TDEEP": "sst",
        "TDEEP_HMODEL": "sst",
    }
    unit_d = {"SST_SST": r"$^{\circ}$C"}

    if plot_list is None:
        plot_list = [str(y) for y in ds.variables]

    for y in ds.variables:
        y = str(y)
        if y in plot_list:
            if "X_" not in y:
                if "Y_" not in y:
                    if "L_" not in y:
                        if "T_" not in y or "SST" in y:
                            if "GRID" != y:
                                print(y)
                                da = ds[y]
                                if (
                                    "T_01" in da.coords
                                    or "T_02" in da.coords
                                    or "T_03" in da.coords
                                    or "T_04" in da.coords
                                ):
                                    for key in da.coords:
                                        num = str(key)[3]
                                    da = da.rename(rdict(num))
                                if y in unit_d:
                                    da.attrs["units"] = unit_d[y]
                                da.coords["x"].attrs["units"] = r"$^{\circ}$E"
                                da.coords["y"].attrs["units"] = r"$^{\circ}$N"
                                da = da.where(da != 0.0).isel(Z=0)
                                da = fix_calendar(da, timevar="time")
                                if "variable" in da.dims:
                                    da = da.isel(variable=0)
                                da = da.rename(y)
                                if y in unit_d:
                                    da.attrs["units"] = unit_d[y]
                                da.attrs["long_name"] = y
                                da.attrs["name"] = y
                                animate_xr_da(
                                    da.isel(
                                        time=slice(front_trim, len(da.time.values))
                                    ),
                                    video_path=os.path.join(
                                        output_dir, file_name + "_" + y + ".gif"
                                    ),
                                    vcmap=cmap_d[y],
                                )


@timeit
def animate_xr_da(
    xr_da: xr.DataArray,
    video_path: str = "output.mp4",
    vcmap: any = cmap("sst"),
) -> None:
    """Animate an `xr.DataArray`.

    Args:
        xr_da (xr.DataArray): input xr.DataArray.
        video_path (str, optional): Video path. Defaults to "output.mp4".
        vcmap (any, optional): cmap for variable. Defaults to cmap("sst").

    """
    ps_defaults(use_tex=False, dpi=200)
    balanced_colormap = False

    if isinstance(vcmap, str):
        if vcmap == "delta":
            balanced_colormap = True
        vcmap = cmap(vcmap)

    assert isinstance(vcmap, matplotlib.colors.LinearSegmentedColormap)

    def gen_frame_func(
        xr_da: xr.DataArray,
    ) -> Callable:
        """Create imageio frame function for `xarray.DataArray` visualisation.

        Args:
            x_da (xr.DataArray): input xr.DataArray.

        Returns:
            make_frame (Callable): function to create each frame.

        """
        vmin = xr_da.min(skipna=True)
        vmax = xr_da.max(skipna=True)
        if balanced_colormap:
            vmin, vmax = [np.min([vmin, -vmax]), np.max([vmax, -vmin])]

        def make_frame(index: int) -> np.array:
            """Make an individual frame of the animation.

            Args:
                index (int): The time index.

            Returns:
                image (np.array): np.frombuffer output that can be fed into imageio

            """
            fig, ax1 = plt.subplots(1, 1)

            xr_da.isel(time=index).plot.imshow(ax=ax1, cmap=vcmap, vmin=vmin, vmax=vmax)
            time_title(ax1, xr_da.time.values[index])
            plt.tight_layout()

            fig.canvas.draw()
            image = np.frombuffer(fig.canvas.tostring_rgb(), dtype="uint8")
            image = image.reshape(fig.canvas.get_width_height()[::-1] + (3,))
            plt.close()

            return image

        return make_frame

    def xarray_to_video(
        xr_da: xr.DataArray,
        video_path: str,
        fps: int = 5,
    ) -> None:
        """Generate video of an `xarray.DataArray`.

        Args:
            xr_da (xr.DataArray): input xarray.DataArray
            video_path (str, optional): output path to save.
            fps (int, optional): frames per second.

        """
        video_indices = list(range(len(xr_da.time.values)))
        make_frame = gen_frame_func(xr_da)
        imageio.mimsave(
            video_path,
            [make_frame(index) for index in tqdm(video_indices, desc=video_path)],
            fps=fps,
        )
        print("Video " + video_path + " made.")

    xarray_to_video(xr_da, video_path, fps=5)
