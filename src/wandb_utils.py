"""Sets up the weights and biases script.

no longer used:

import wandb_summarizer.download
"""
from typing import Optional, List
import math
import numpy as np
import pandas as pd
import wandb
import logging
from omegaconf import DictConfig
from subprocess import PIPE, run
from src.constants import DATA_PATH, run_path


log = logging.getLogger(__name__)


def get_v(inp: str) -> str:
    """Get version of compilers.

    Args:
        inp (str): input string. E.g. "gfortran -v".

    Returns:
        str: selects the fortran version (or gcc version)
            part of the output.
    """
    # pylint: disable=subprocess-run-check
    return run(
        inp, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True
    ).stderr.split("\n")[-2]


def start_wandb(cfg: DictConfig, unit_test: bool = False) -> None:
    """
    Intialises wandb for run.

    Weights and biases provides the run tracking for the model runs at different
    parameter settings.

    TODO: Need to improve the ability to initialise wandb from a unit test.

    Args:
        cfg (DictConfig): The config settings to pass in to the wandb syncing.
        unit_test (bool, optional): Whether or not this is a unit-test.
            Defaults to False. If this is a unit test will currently not initialise
            wandb, but will call related functions.

    """

    if not unit_test:

        wandb.init(
            project=cfg.project,
            entity=cfg.user,
            dir=run_path(cfg, unit_test=unit_test),
            save_code=True,
            name=cfg.name,
            notes=cfg.notes,
            # pylint: disable=protected-access
            config=cfg._content,
        )

        wandb.config.update({"gfortran": get_v("gfortran -v"), "gcc": get_v("gcc -v")})
    else:
        print({"gfortran": get_v("gfortran -v"), "gcc": get_v("gcc -v")})


def get_full_csv() -> pd.DataFrame:
    """
    Get the full csv.
    """
    api = wandb.Api()

    # Project is specified by <entity/project-name>
    runs = api.runs("sdat2/seager19")
    summary_list = []
    config_list = []
    name_list = []

    for rn in runs:

        # run.summary are the output key/values like accuracy.
        # We call ._json_dict to omit large files
        # pylint: disable=protected-access
        summary_list.append(rn.summary._json_dict)

        # run.config is the input metrics.
        # We remove special values that start with _.
        config = {k: v for k, v in rn.config.items() if not k.startswith("_")}
        config_list.append(config)

        # run.name is the name of the run.
        name_list.append(rn.name)

    summary_df = pd.DataFrame.from_records(summary_list)
    config_df = pd.DataFrame.from_records(config_list)
    name_df = pd.DataFrame({"name": name_list})
    all_df = pd.concat([name_df, config_df, summary_df], axis=1)

    all_df.to_csv(DATA_PATH / "project.csv")

    return all_df


def get_wandb_data(save_path: Optional[str] = None) -> pd.DataFrame:
    """
    Get wandb data (and save it?) now doesn't redownload.

    Args:
        save_path (Optional[str], optional): Path to new csv file. Defaults to None.
            If it is None then doesn't try to save.

    Returns:
        pd.DataFrame: The pandas dataframe of final results.
    """
    # run_info = wandb_summarizer.download.get_results("sdat2/seager19")
    # df = pd.DataFrame(run_info)
    # if save_path is not None:
    #    df.to_csv(save_path)

    df = pd.read_csv(save_path)

    return df


# pylint: disable=dangerous-default-value
def metric_conv_data(
    metric_name: str = "mean_pac",
    prefix: str = "cd_",
    ex_list: List[str] = [
        "cd_norm",
        "nummode",
    ],
    control_variable_list=[(("atm", "k_days"), 10)],
    index_by: tuple = ("coup", "c_d"),
) -> dict:
    """
    Generate the data for the convergence of a particular item.

    Used in src.visualisation.convergence.metric_conv_plot

    Args:
        metric_name (str, optional): Which keyword to use. Defaults to "mean_pac".

    Returns:
        dict: A dictionary with the relevant metrics in.
    """
    api = wandb.Api()
    # Project is specified by <entity/project-name>

    def check_controls(config):
        truth_list = []
        for i in control_variable_list:
            print(i)
            print([i[0][0], i[0][1]])
            # pylint: disable=eval-used
            af = eval(config[i[0][0]])[i[0][1]]
            print(af, i[1], af == i[1])
            truth_list.append(af == i[1])
        return np.all(truth_list)

    runs = api.runs("sdat2/seager19")
    metric_dict = {}

    # pylint: disable=unnecessary-comprehension
    for rn in runs:  # [x for x in runs][0:13]:
        if prefix in rn.name and np.all([x not in rn.name for x in ex_list]):
            print(rn.name)
            config = {k: v for k, v in rn.config.items() if not k.startswith("_")}
            # print(rn, config["name"])
            pair_list = []
            for _, row in rn.history().iterrows():
                step = row["_step"]
                metric = row[metric_name]
                if not math.isnan(metric):
                    # print(step, metric, type(metric))
                    pair_list.append([step, metric])

            # enforce needing 6 iterations.
            if len(pair_list) == 6:
                # pylint: disable=eval-used
                if check_controls(config):
                    metric_dict[eval(config[index_by[0]])[index_by[1]]] = np.array(
                        pair_list
                    )

    return metric_dict


if __name__ == "__main__":
    # python src/wandb_utils.py
    # add control variables
    print(metric_conv_data())
    print(
        metric_conv_data(
            metric_name="trend_nino3",
            prefix="days_",
            ex_list=["k_days_", "days_10", "days_5", "days_3"],
            index_by=("atm", "eps_days"),
        )
    )
    metric_d = metric_conv_data(
        metric_name="trend_nino3.4",
        prefix="k_days_",
        control_variable_list=[(("atm", "eps_days"), 0.75)],
        index_by=("atm", "k_days"),
    )
    # pylint: disable=condider-using-dict-items
    for val in metric_d:
        print(val, float(metric_d[val][5, 1]))
