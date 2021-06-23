"""Look at the convergence of the coupling scheme."""
from typing import Callable
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from src.wandb_utils import metric_conv_data
from src.constants import FIGURE_PATH, CD_LOGS
from src.xr_utils import open_dataarray, open_dataset, sel
from src.plot_utils import (
    ps_defaults,
    cmap,
    add_units,
    get_dim,
    label_subplots,
)
from src.configs.load_config import load_config
from src.models.model_setup import ModelSetup


ps_defaults(use_tex=False, dpi=200)


def metric_conv_plot(
    metric_name: str = "mean_pac",
    long_name: str = "Mean Tropical Pacific (pac)",
    show_plots: bool = False,
):
    """
    Make the convergence plot for a particular metric.

    Args:
        metric_name (str, optional): The keyword to extract. Defaults to "mean_pac".
        long_name (str, optional): The long name for the ylabel.
            Defaults to "Mean Tropical Pacific (pac)".
    """

    metric_dict = metric_conv_data(metric_name=metric_name)

    for cd in sorted(metric_dict):
        plt.plot(
            metric_dict[cd][:, 0], metric_dict[cd][:, 1], label="{:.2e}".format(cd)
        )

    plt.legend(
        bbox_to_anchor=(-0.15, 1.02, 1.15, 0.102),
        loc="lower left",
        mode="expand",
        ncol=5,
    )
    plt.xlabel("Step")
    plt.ylabel(long_name + r" [$^{\circ}$C]")
    plt.tight_layout()
    plt.savefig(FIGURE_PATH / str(metric_name + "_convergence.png"))
    plt.savefig(FIGURE_PATH / str(metric_name + "_convergence.pdf"))

    if show_plots:
        plt.show()
    else:
        plt.clf()

    for cd in metric_dict:
        plt.plot(
            np.abs(
                (metric_dict[cd][:, 1] - metric_dict[cd][5, 1]) / metric_dict[cd][5, 1]
            ),
            label="{:.2e}".format(cd),
        )
    plt.ylabel(long_name + r" $ \frac{|C-F|}{F}$")
    plt.yscale("log")
    plt.xlabel("Step")
    plt.legend(
        bbox_to_anchor=(-0.15, 1.02, 1.15, 0.102),
        loc="lower left",
        mode="expand",
        ncol=5,
    )
    plt.tight_layout()
    plt.savefig(FIGURE_PATH / str(metric_name + "_convergence_log.png"))
    plt.savefig(FIGURE_PATH / str(metric_name + "_convergence_log.pdf"))

    if show_plots:
        plt.show()
    else:
        plt.clf()


def coupling_frame(
    setup: ModelSetup,
    pac: bool = False,
    mask_land: bool = False,
    close_figure: bool = True,
) -> Callable:
    """Create imageio frame function.

    Returns:
        Callable: make_frame function to create each frame.

    """

    mask = open_dataset(setup.om_mask()).mask

    def clip(da: xr.DataArray) -> xr.DataArray:
        if pac and not mask_land:
            return sel(da)
        elif pac and mask_land:
            return sel(da).where(sel(mask) != 0.0)
        elif not pac and mask_land:
            return da.where(mask != 0.0)  # may not work if they have different grids.
        else:
            return da

    def make_frame(index: int) -> np.ndarray:
        """Make an individual frame of the animation.

        Args:
            index (int): index.

        Returns:
            image (np.ndarray): np.frombuffer output that can be fed into imageio.

        """
        cbar_dict = {
            "extend": "neither",  #  "both",
            "extendfrac": 0.0,
            "extendrect": True,
        }
        fig, axs = plt.subplots(3, 2, figsize=get_dim(ratio=(5 ** 0.5 - 1) / 2 * 1.5))
        plt.suptitle("Iteration: " + str(index))
        clip(add_units(open_dataarray(setup.tau_y(it=index)).isel(T=600))).plot(
            ax=axs[0, 0],
            cmap=cmap("delta"),
            vmin=-0.6,
            vmax=0.6,
            cbar_kwargs=cbar_dict,
        )
        axs[0, 0].set_title(r"$\tau_y$ [Pa]")
        axs[0, 0].set_xlabel("")
        clip(add_units(open_dataarray(setup.tau_x(it=index)).isel(T=600))).plot(
            ax=axs[0, 1],
            cmap=cmap("delta"),
            vmin=-0.9,
            vmax=0.9,
            cbar_kwargs=cbar_dict,
        )
        axs[0, 1].set_title(r"$\tau_x$ [Pa]")
        axs[0, 1].set_xlabel("")
        axs[0, 1].set_ylabel("")
        clip(add_units(open_dataarray(setup.dq_df(it=index)).isel(T=1))).plot(
            ax=axs[1, 0],
            cmap=cmap("sst"),
            vmin=180,
            vmax=450,
            cbar_kwargs=cbar_dict,
        )
        axs[1, 0].set_title(r"$\frac{dQ}{df}$ [W m$^{-2}$]")
        axs[1, 0].set_xlabel("")
        clip(add_units(open_dataarray(setup.dq_dt(it=index)).isel(T=1))).plot(
            ax=axs[1, 1], cmap=cmap("sst"), vmin=0, vmax=7.5, cbar_kwargs=cbar_dict
        )
        axs[1, 1].set_title(r"$\frac{dQ}{dT}$ [W m$^{-2}$ K$^{-1}$]")
        axs[1, 1].set_xlabel("")
        axs[1, 1].set_ylabel("")
        clip(add_units(open_dataarray(setup.ts_clim(it=index)))).plot(
            ax=axs[2, 0],
            cmap=cmap("sst"),
            vmin=270,
            vmax=310,
            cbar_kwargs=cbar_dict,
        )
        axs[2, 0].set_title(r"$\bar{T}_s$ [K]")
        clip(add_units(open_dataarray(setup.ts_trend(it=index)))).plot(
            ax=axs[2, 1], cmap=cmap("delta"), vmin=-5, vmax=5, cbar_kwargs=cbar_dict
        )
        axs[2, 1].set_title(r"$\Delta T_s$ [$\Delta$ K]")
        axs[2, 1].set_ylabel("")
        plt.tight_layout()
        label_subplots(axs, y_pos=1.25, x_pos=-0.15)
        fig.canvas.draw()
        image = np.frombuffer(fig.canvas.tostring_rgb(), dtype="uint8")
        image = image.reshape(fig.canvas.get_width_height()[::-1] + (3,))

        if close_figure:
            plt.close()

        return image

    return make_frame


def final_coup_plot() -> None:
    """
    Final coup plot.
    """
    direc = CD_LOGS / "cd_2.25" / "wandb" / "latest-run" / "files"
    cfg = load_config(test=False)
    setup = ModelSetup(direc, cfg, make_move=False)
    make_frame = coupling_frame(
        setup,
        close_figure=False,
    )
    _ = make_frame(5)
    plt.savefig(FIGURE_PATH / "cd_2.25_coup.pdf")
    plt.savefig(FIGURE_PATH / "cd_2.25_coup.png")
    plt.clf()
    make_frame = coupling_frame(
        setup,
        pac=True,
        mask_land=True,
        close_figure=False,
    )
    _ = make_frame(5)
    plt.savefig(FIGURE_PATH / "cd_2.25_pac_mask_land_coup.pdf")
    plt.savefig(FIGURE_PATH / "cd_2.25_pac_mask_land_coup.png")
    plt.clf()


if __name__ == "__main__":
    # python src/visualisation/convergence.py
    # metric_conv_plot()
    # metric_conv_plot(metric_name="trend_nino3.4", long_name="Trend nino3.4")
    final_coup_plot()
