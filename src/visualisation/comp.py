"""Program to do."""
import os
import xarray as xr
import matplotlib.pyplot as plt
import np

# Get the helper functions
from typing import List
from src.models.model_setup import ModelSetup
from src.xr_utils import open_dataset, open_dataarray, get_trend, clip, can_coords, sel
from src.utils import get_default_setup
from src.configs.load_config import load_config
from src.plot_utils import add_units, cmap, get_dim, label_subplots
from src.constants import UC_LOGS, FIGURE_DATA_PATH


def get_setups():
    uncoupled_run_dir = str(UC_LOGS / "it_1")
    uc_2_dr = str(UC_LOGS / "pap_2")
    cfg = load_config(test=False)
    uc2_stp = ModelSetup(uc_2_dr, cfg, make_move=False)
    uncoup_setup = ModelSetup(uncoupled_run_dir, cfg, make_move=False)
    coup_setup = get_default_setup()


def comp_plot(
    ours: xr.DataArray,
    papers: xr.DataArray,
    default_cmap="delta",
    diff_cmap="delta",
    **kwargs
) -> None:
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


def return_var_list(num: int) -> List[str]:
    var_list = []
    for var in xr.open_dataset(FIGURE_DATA_PATH):
        if "Fig_" + str(num) in var:
            var_list.append(var)
    return var_list


def comp_uc_oc(setup: ModelSetup, panel="d"):
    fig_data = xr.open_dataset(FIGURE_DATA_PATH)
    uc_oc = xr.open_dataset(setup.om_run2f_nc(), decode_times=False)
    uc_oc_dt = add_units(get_trend(clip(can_coords(uc_oc.SST_SST))).isel(Z=0).drop("Z"))
    uc_oc_dt.attrs["units"] = "$\Delta$ K"
    uc_oc_dt.attrs["long_name"] = r"$\Delta$ SST"
    ddata = add_units(
        sel(
            can_coords(fig_data["ForcedOceanModel.sst-trend-Fig_1" + panel + ".nc.SST"])
        )
    )
    ddata = ddata.where(ddata != 0.0).rename(r"$\Delta$ SST")
    ddata.attrs["units"] = "$\Delta$ K"
    ddata.attrs["long_name"] = r"$\Delta$ SST"
    comp_plot(add_units(uc_oc_dt.interp_like(ddata)), ddata)


def comp_uc_atm(setup: ModelSetup, panel="d"):
    fig_data = xr.open_dataset(FIGURE_DATA_PATH)
    uc_atm = open_dataset(setup.tcam_output())
    prtrend_o = clip(can_coords(uc_atm.PRtrend))
    prtrend_p = clip(
        can_coords(fig_data["ForcedAtmosphereModel.Fig_2" + panel + ".nc.PRtrend"])
    )
    comp_plot(prtrend_o, prtrend_p, default_cmap="ranom")
    vtrend_o = clip(can_coords(uc_atm.vtrend))
    vtrend_p = clip(
        can_coords(fig_data["ForcedAtmosphereModel.Fig_2" + panel + ".nc.vtrend"])
    )
    comp_plot(vtrend_o, vtrend_p)
    utrend_o = clip(can_coords(uc_atm.utrend))
    utrend_p = clip(can_coords(fig_data["ForcedAtmosphereModel.Fig_2d.nc.utrend"]))
    comp_plot(utrend_o, utrend_p)
