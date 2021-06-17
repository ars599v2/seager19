"""ani.py - A set of functions to animate particular results.

animate_xr_da - animation for individual xr.DataArray.

animate_prediction - plots inputs and outputs of old model.

"""
import os
import pathlib
from typing import Callable, Optional, Union
import numpy as np
import xarray as xr
from tqdm import tqdm
import matplotlib
import matplotlib.pyplot as plt
from typeguard import typechecked
import imageio
from src.plot_utils import (
    ps_defaults,
    time_title,
    cmap,
    add_units,
    get_dim,
    label_subplots,
)
from src.utils import timeit
from src.xr_utils import fix_calendar, open_dataarray, can_coords
from src.constants import OCEAN_DATA_PATH, GIF_PATH
from src.models.model_setup import ModelSetup


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
        front_trim (int): the number of T indices to remove from the front of the
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
                                da = can_coords(da)
                                if y in unit_d:
                                    da.attrs["units"] = unit_d[y]
                                da = add_units(da)
                                da = da.where(da != 0.0).isel(Z=0)
                                da = fix_calendar(da, timevar="T")
                                if "variable" in da.dims:
                                    da = da.isel(variable=0)
                                da = da.rename(y)
                                if y in unit_d:
                                    da.attrs["units"] = unit_d[y]
                                da.attrs["long_name"] = y
                                da.attrs["name"] = y
                                animate_xr_da(
                                    da.isel(T=slice(front_trim, len(da.T.values))),
                                    video_path=os.path.join(
                                        output_dir, file_name + "_" + y + ".gif"
                                    ),
                                    vcmap=cmap_d[y],
                                    dpi=dpi,
                                )

    # pylint: disable=pointless-string-statement
    """
    excl_l = ["X_", "Y_", "L_", "T_", "GRID"]  # SST

    t_pos = ["T_01", "T_02", "T_03", "T_04"]

    for y in ds.variables:
        y = str(y)
        if np.all([x not in y for x in excl_l]) and y in plot_list:
            da = ds[y]
            if np.any([x in da.coords for x in t_pos]):
                for key in da.coords:
                    num = str(key)[3]
                da = da.rename(om_rdict(num))
                if y in unit_d:
                    da.attrs["units"] = unit_d[y]
                da = add_units(da)
                da = da.where(da != 0.0).isel(Z=0)
                da = fix_calendar(da, timevar="T")
                if "variable" in da.dims:
                    da = da.isel(variable=0)
                da = da.rename(y)
                if y in unit_d:
                    da.attrs["units"] = unit_d[y]
                da.attrs["long_name"] = y
                da.attrs["name"] = y
                animate_xr_da(
                    da.isel(T=slice(front_trim, len(da.T.values))),
                    video_path=os.path.join(output_dir, file_name + "_" + y + ".gif"),
                    vcmap=cmap_d[y],
                    dpi=dpi,
                )
    """


@timeit
def animate_xr_da(
    xr_da: xr.DataArray,
    video_path: str = "output.mp4",
    vcmap: Union[str, matplotlib.colors.LinearSegmentedColormap] = cmap("sst"),
    dpi: float = 200,
) -> None:
    """Animate an `xr.DataArray`.

    Args:
        xr_da (xr.DataArray): input xr.DataArray.
        video_path (str, optional): Video path. Defaults to "output.mp4".
        vcmap (Union[str, matplotlib.colors.LinearSegmentedColormap], optional):
            cmap for variable. Defaults to cmap("sst").
        dpi (float, optional): dots per inch for plotting. Defaults to 200.

    """
    ps_defaults(use_tex=False, dpi=dpi)
    balanced_colormap = False

    xr_da = add_units(xr_da)

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

        @typechecked
        def make_frame(index: int) -> np.ndarray:
            """Make an individual frame of the animation.

            Args:
                index (int): The T index.

            Returns:
                image (np.array): np.frombuffer output
                    that can be fed into imageio

            """
            fig, ax1 = plt.subplots(1, 1)

            xr_da.isel(T=index).plot.imshow(ax=ax1, cmap=vcmap, vmin=vmin, vmax=vmax)
            time_title(ax1, xr_da.coords["T"].values[index])
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
        video_indices = list(range(len(xr_da.coords["T"].values)))
        make_frame = gen_frame_func(xr_da)
        imageio.mimsave(
            video_path,
            [make_frame(index) for index in tqdm(video_indices, desc=video_path)],
            fps=fps,
        )
        print("Video " + video_path + " made.")

    xarray_to_video(xr_da, video_path, fps=5)


@timeit
def animate_qflx_diff(
    path_a: Union[str, pathlib.Path] = os.path.join(OCEAN_DATA_PATH, "qflx.nc"),
    path_b: Union[str, pathlib.Path] = os.path.join(OCEAN_DATA_PATH, "qflx-0.nc"),
    video_path: str = os.path.join(GIF_PATH, "diff-output.gif"),
    fps: int = 5,
    dpi: int = 200,
) -> None:
    """
    Animate two `xr.DataArray` and the difference between them.

    Args:
        path_a (Union[str, pathlib.Path], optional): Path to qflx. Defaults to
            os.path.join(OCEAN_DATA_PATH, "qflx.nc").
        path_b (Union[str, pathlib.Path], optional): Path to qflx-0. Defaults to
            os.path.join(OCEAN_DATA_PATH, "qflx-0.nc").
        video_path (str, optional): path to save video to. Defaults to
            os.path.join(GIF_PATH, "diff-output.gif").
        fps (int, optional): Frames per second. Defaults to 5.
        dpi (int, optional): dots per inch. Defaults to 200.
    """
    ps_defaults(use_tex=False, dpi=dpi)

    qflx = open_dataarray(path_a)
    qflx_0 = open_dataarray(path_b)
    diff = qflx - qflx_0

    da = xr.concat([qflx.isel(Z=0), qflx_0.isel(Z=0), diff.isel(Z=0)], dim="flux")
    da = (
        da.assign_coords(coords={"flux": ["qflx", "qflx_0", "qflx - qflx_0"]})
        .isel(variable=0)
        .drop(labels="Z")
    )

    da = add_units(da)

    vmin, vmax = -0.0002, 0.0002

    def gen_frame_func(xr_da: xr.DataArray) -> Callable:
        """Create imageio frame function for `xarray.DataArray` visualisation.

        Args:
            xr_da (xr.DataArray): input xr.DataArray.

        Returns:
            Callable: make_frame function to create each frame.

        """

        def make_frame(index: int) -> np.array:
            """Make an individual frame of the animation.

            Args:
                index (int): The T index.

            Returns:
                image (np.array): np.frombuffer output that can be fed into imageio

            """
            xr_da.isel(T=index).sel(X=slice(100, 290), Y=slice(-30, 30)).plot(
                row="flux",
                vmin=vmin,
                vmax=vmax,
                cmap="RdBu",
                aspect=2,
                cbar_kwargs={
                    "shrink": 1,
                    "aspect": 35,
                    "label": "qflx [dimensionless]",
                    # further options available here:
                    # https://matplotlib.org/stable/api/_as_gen/
                    # matplotlib.pyplot.colorbar.html
                    "extend": "neither",  #  "both",
                    "extendfrac": 0.0,
                    "extendrect": True,
                    "format": "%0.1e",
                },
            )

            plt.suptitle(
                xr_da.coords["T"].values[index].strftime()[0:10], x=0.75, y=0.98
            )

            # plt.tight_layout()

            fig = plt.gcf()

            fig.canvas.draw()
            image = np.frombuffer(fig.canvas.tostring_rgb(), dtype="uint8")
            image = image.reshape(fig.canvas.get_width_height()[::-1] + (3,))
            plt.close()

            return image

        return make_frame

    video_indices = list(range(len(da.coords["T"].values)))
    make_frame = gen_frame_func(da)
    imageio.mimsave(
        video_path,
        [make_frame(index) for index in tqdm(video_indices, desc=video_path)],
        fps=fps,
    )
    print("Video " + video_path + " made.")


@timeit
def animate_coupling(setup: ModelSetup, dpi: int = 200) -> None:
    """
    Animatie coupling.

    Args:
        setup (ModelSetup): setup object.
        dpi (int, optional): Dots per inch. Defaults to 200.

    """
    ps_defaults(use_tex=False, dpi=dpi)

    def gen_frame_func() -> Callable:
        """Create imageio frame function.

        Returns:
            Callable: make_frame function to create each frame.

        """

        def make_frame(index: int) -> np.array:
            """Make an individual frame of the animation.

            Args:
                index (int): index.

            Returns:
                image (np.array): np.frombuffer output that can be fed into imageio

            """
            fig, axs = plt.subplots(
                3, 2, figsize=get_dim(ratio=(5 ** 0.5 - 1) / 2 * 1.5)
            )
            plt.suptitle("Iteration: " + str(index))
            add_units(open_dataarray(setup.tau_y(it=index)).isel(T=1)).plot(
                ax=axs[0, 0], cmap=cmap("delta")
            )
            axs[0, 0].set_title(r"$\tau_y$ [Pa]")
            axs[0, 0].set_xlabel("")
            add_units(open_dataarray(setup.tau_x(it=index)).isel(T=1)).plot(
                ax=axs[0, 1], cmap=cmap("delta")
            )
            axs[0, 1].set_title(r"$\tau_x$ [Pa]")
            axs[0, 1].set_xlabel("")
            axs[0, 1].set_ylabel("")
            add_units(open_dataarray(setup.dq_df(it=index)).isel(T=1)).plot(
                ax=axs[1, 0], cmap=cmap("sst")
            )
            axs[1, 0].set_title(r"$\frac{dQ}{df}$ [W m$^{-2}$]")
            axs[1, 0].set_xlabel("")
            add_units(open_dataarray(setup.dq_dt(it=index)).isel(T=1)).plot(
                ax=axs[1, 1], cmap=cmap("sst")
            )
            axs[1, 1].set_title(r"$\frac{dQ}{dT}$ [W m$^{-2}$ K$^{-1}$]")
            axs[1, 1].set_xlabel("")
            axs[1, 1].set_ylabel("")
            add_units(open_dataarray(setup.ts_clim(it=index))).plot(
                ax=axs[2, 0], cmap=cmap("sst")
            )
            axs[2, 0].set_title(r"$\bar{T}_s$ [K]")
            add_units(open_dataarray(setup.ts_trend(it=index))).plot(
                ax=axs[2, 1], cmap=cmap("sst")
            )
            axs[2, 1].set_title(r"Trend $T_s$ [K]")
            axs[2, 1].set_ylabel("")
            plt.tight_layout()
            label_subplots(axs, y_pos=1.08, x_pos=-0.15)
            fig.canvas.draw()
            image = np.frombuffer(fig.canvas.tostring_rgb(), dtype="uint8")
            image = image.reshape(fig.canvas.get_width_height()[::-1] + (3,))
            plt.close()

            return image

        return make_frame

    video_indices = list(range(len(setup.cfg.coup.iterations)))
    video_path = os.path.join(setup.gif_path, "coupling.gif")
    make_frame = gen_frame_func()
    imageio.mimsave(
        video_path,
        [make_frame(index) for index in tqdm(video_indices, desc=video_path)],
        fps=2,
    )
    print("Video " + video_path + " made.")
