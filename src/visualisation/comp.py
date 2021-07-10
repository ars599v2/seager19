"""Program to automate testing output fields against the paper."""
from typing import Union
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from typing import List
from src.models.model_setup import ModelSetup
from src.xr_utils import open_dataset, get_trend, clip, can_coords, sel
from src.utils import get_default_setup
from src.configs.load_config import load_config
from src.plot_utils import add_units, cmap, get_dim, label_subplots, ps_defaults
from src.constants import UC_LOGS, FIGURE_DATA_PATH
from src.visualisation.quiver import pqp_part


def comp_plot(
    ours: xr.DataArray,
    papers: xr.DataArray,
    default_cmap="delta",
    diff_cmap="delta",
    **kwargs
) -> None:
    """
    A comparison plot for two scalar fields.

    Args:
        ours (xr.DataArray): The output of the model.
        papers (xr.DataArray): The paper's values.
        default_cmap (str, optional): The colormap for the field.
            Defaults to "delta".
        diff_cmap (str, optional): The colormap for the difference
            between the two fields. Defaults to "delta".
    """
    ours, papers = add_units(ours), add_units(papers)
    _, axs = plt.subplots(4, figsize=get_dim(ratio=0.3 * 4), sharex=True)
    ours.plot(ax=axs[0], cmap=cmap(default_cmap), **kwargs)
    axs[0].set_xlabel("")
    papers.plot(ax=axs[1], cmap=cmap(default_cmap), **kwargs)
    axs[1].set_xlabel("")
    (ours - papers).plot(ax=axs[2], cmap=cmap(diff_cmap), **kwargs)
    axs[2].set_xlabel("")
    np.abs((ours - papers) / papers).plot(ax=axs[3], vmin=0, vmax=1, cmap=cmap("sst"))
    label_subplots(axs, y_pos=1.05, x_pos=-0.1)
    plt.tight_layout()


def comp_prcp_quiver_plot(
    ours: xr.Dataset, theirs: xr.Dataset, vmin=-5e-5, vmax=5e-5, x_pos=0.73, y_pos=-0.15
) -> None:
    """
    Compare the precipitation and windspeeds.

    Args:
        ours (xr.Dataset): Our dataset.
        theirs (xr.Dataset): Their dataset.
    """
    ps_defaults(use_tex=False, dpi=200)
    _, axs = plt.subplots(3, 1, figsize=get_dim(ratio=0.3 * 3), sharex=True)
    pqp_part(axs[0], ours, x_pos=x_pos, y_pos=y_pos, vmin=vmin, vmax=vmax)
    axs[0].set_xlabel("")
    pqp_part(axs[1], theirs, x_pos=x_pos, y_pos=y_pos, vmin=vmin, vmax=vmax)
    axs[1].set_xlabel("")
    diff = ours.copy()
    diff["utrend"] = ours["utrend"] - theirs["utrend"]
    diff["vtrend"] = ours["vtrend"] - theirs["vtrend"]
    diff["PRtrend"] = ours["PRtrend"] - theirs["PRtrend"]
    pqp_part(axs[2], diff, x_pos=x_pos, y_pos=-0.3, vmin=vmin, vmax=vmax)
    label_subplots(axs, y_pos=1.05, x_pos=-0.18)
    plt.tight_layout()


def return_var_list(num: Union[int, str]) -> List[str]:
    """
    Get a list of the variables from each figure.

    Args:
        num Union[int, str]: The figure number.
            Example input: int(4) or "2a".

    Returns:
        List[str]: A list of the variable names.
    """
    var_list = []
    for var in xr.open_dataset(FIGURE_DATA_PATH):
        if "Fig_" + str(num) in var:
            var_list.append(var)
    return var_list


def return_figure_ds(num: str) -> xr.Dataset:
    """
    Get the figure dataset.

    Args:
        num (str): The figure number e.g. "2c".

    Returns:
        xr.Dataset: the dataset with the standard names.
    """
    ps_defaults(use_tex=False, dpi=200)
    fig_data = xr.open_dataset(FIGURE_DATA_PATH)
    r_dict = {}
    for i in fig_data[return_var_list(num)]:
        r_dict[i] = i.split(".")[-1]

    return fig_data[return_var_list(num)].rename(r_dict)


def comp_uc_oc(setup: ModelSetup, panel="d") -> None:
    """
    Test to see if panel 1d is replicated.

    Args:
        setup (ModelSetup): The setup object.
        panel (str, optional): Which panel to test aginst. Defaults to "d".
    """
    ps_defaults(use_tex=False, dpi=200)
    fig_data = xr.open_dataset(FIGURE_DATA_PATH)
    uc_oc = xr.open_dataset(setup.om_run2f_nc(), decode_times=False)
    uc_oc_dt = add_units(get_trend(clip(can_coords(uc_oc.SST_SST))).isel(Z=0).drop("Z"))
    uc_oc_dt.attrs["units"] = r"$\Delta$ K"
    uc_oc_dt.attrs["long_name"] = r"$\Delta$ SST"
    ddata = add_units(
        sel(
            can_coords(fig_data["ForcedOceanModel.sst-trend-Fig_1" + panel + ".nc.SST"])
        )
    )
    ddata = ddata.where(ddata != 0.0).rename(r"$\Delta$ SST")
    ddata.attrs["units"] = r"$\Delta$ K"
    ddata.attrs["long_name"] = r"$\Delta$ SST"
    comp_plot(add_units(uc_oc_dt.interp_like(ddata)), ddata)


def comp_uc_atm(setup: ModelSetup, panel="d") -> None:
    """
    Test to see if panel 2d is right.

    Args:
        setup (ModelSetup): The path object.
        panel (str, optional): Which panel to test against. Defaults to "d".
    """
    ps_defaults(use_tex=False, dpi=200)
    uc_atm = open_dataset(setup.tcam_output())
    ads = return_figure_ds("2" + panel)
    comp_prcp_quiver_plot(uc_atm, ads)
    plt.savefig("example.png")


def comp_atm(setup: ModelSetup, num: str) -> None:
    """
    Test to see if atm is right.

    Args:
        setup (ModelSetup): The path object.
        panel (str): Which panel to test against. E.g. 2d.
    """
    ps_defaults(use_tex=False, dpi=200)
    uc_atm = open_dataset(setup.tcam_output())
    ads = return_figure_ds(num)
    comp_prcp_quiver_plot(uc_atm, ads)
    plt.savefig("example-atm.png")


def comp_oc(setup: ModelSetup, num: str) -> None:
    """
    Compare the sea surface temperature trend of the final model iteration.

    Args:
        setup (ModelSetup): The setup.
        num (str): The number e.g. "2b".
    """
    ps_defaults(use_tex=False, dpi=200)
    uc_oc = xr.open_dataset(setup.om_run2f_nc(), decode_times=False)
    oc_dt = add_units(get_trend(clip(can_coords(uc_oc.SST_SST))).isel(Z=0).drop("Z"))
    oc_dt.attrs["units"] = r"$\Delta$ K"
    oc_dt.attrs["long_name"] = r"$\Delta$ SST"
    ds = return_figure_ds(num)
    ddata = add_units(sel(can_coords(ds["tstrend"])))
    ddata = ddata.where(ddata != 0.0).rename(r"$\Delta$ SST")
    ddata.attrs["units"] = r"$\Delta$ K"
    ddata.attrs["long_name"] = r"$\Delta$ SST"
    comp_plot(add_units(oc_dt.interp_like(ddata)), ddata, vmin=-2, vmax=2)
    plt.savefig("example-oc.png")


if __name__ == "__main__":
    # python src/visualisation/comp.py
    uncoupled_run_dir = str(UC_LOGS / "it_1")
    cfg = load_config(test=False)
    uncoup_setup = ModelSetup(uncoupled_run_dir, cfg, make_move=False)
    coup_setup = get_default_setup()
    # comp_uc_atm(uncoup_setup)
    comp_oc(coup_setup, "3")
    comp_atm(coup_setup, "3")
    # comp_uc_oc(uncoup_setup)
