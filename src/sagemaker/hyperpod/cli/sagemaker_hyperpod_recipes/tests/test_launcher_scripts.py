# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import logging
from typing import Optional

from launcher.nemo.constants import ROOT_DIR

from .test_utils import (
    get_launcher_run_script_paths,
    is_job_run_name_valid_for_clusters,
)

logger = logging.getLogger(__name__)

RUN_SCRIPT_PATHS = get_launcher_run_script_paths()


def test_config_for_run_script_exists():
    RECIPES_DIR = ROOT_DIR / "recipes_collection/recipes"
    log_line = lambda script, config: logger.info(
        f"\nlauncher file: {script.relative_to(ROOT_DIR)}" f"\nconfig file: {config.relative_to(ROOT_DIR)}" "\n"
    )

    def extract_value_in_line(line: str) -> str:
        _, value = line.split("=")
        value = value.replace(" \\", "")  # remove shell line continuation marker
        value = value.strip()
        return value

    def assert_recipe_config_exists(line: str, config_path_str: str):
        # Example:
        # recipes=training/llama/hf_llama3_2_90b_seq8k_gpu_p5x32_pretrain
        config_path = RECIPES_DIR / (config_path_str + ".yaml")  # append .yaml
        assert config_path.exists(), log_line(run_script_path, config_path)

    def assert_run_name_is_valid(line: str, config_path_str: Optional[str]):
        """
        Ensure the name is valid for Slurm and Kubernetes clusters
        """
        # Example:
        #    recipes.run.name="hf-llama3-70b-lora" \
        run_name = extract_value_in_line(line)
        run_name = run_name.replace('"', "")  # remove quotes
        run_name = run_name.strip()

        if config_path_str is None:
            config_path_str = "config_file_not_defined"

        config_path = RECIPES_DIR / (config_path_str + ".yaml")  # append .yaml
        assert is_job_run_name_valid_for_clusters(run_name), log_line(run_script_path, config_path)

    for run_script_path in RUN_SCRIPT_PATHS:
        with open(run_script_path, "r") as fd:
            for line in fd:
                config_path_str = None

                if "recipes=" in line:
                    config_path_str = extract_value_in_line(line)
                    assert_recipe_config_exists(line, config_path_str)

                if "recipes.run.name=" in line:
                    assert_run_name_is_valid(line, config_path_str)
