"""Test `src.visualisation.ani.py`.

Example:
    Call from command line::

        pytest src/test/test_ani.py

"""
import os
import xarray as xr
from src.visualisation.ani import animate_xr_da, animate_ds, animate_qflx_diff
from src.constants import OCEAN_OUTPUT_PATH, GIF_PATH
from src.data_loading.download import get_data
from src.xr_utils import can_coords


def test_animate_xr_da() -> None:
    """Test `src.visualisation.ani.animate_xr_da`."""
    da = (
        can_coords(xr.tutorial.load_dataset("air_temperature").air).isel(T=slice(0, 5))
        - 150
    ) / 150
    animate_xr_da(da, video_path="gifs/test_output.mp4")
    animate_xr_da(da, video_path="gifs/test_output.gif")


def test_animate_ds() -> None:
    """Animate the sst into gifs."""
    get_data()

    for x in [
        "om_diag",
    ]:
        animate_ds(
            xr.open_dataset(
                str(os.path.join(OCEAN_OUTPUT_PATH, x)) + ".nc", decode_times=False
            ),
            x,
            GIF_PATH,
            dpi=200,
            front_trim=1,
            plot_list=["SST_QFLX"],
        )


def test_animate_qflx() -> None:
    """Animate qflx."""
    animate_qflx_diff()


if __name__ == "__main__":
    test_animate_ds()
    test_animate_xr_da()
