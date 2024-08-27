from pathlib import Path
from typing import List

import nemo_launcher.utils.job_utils as job_utils
from nemo_launcher.core.launchers import AutoLauncher, K8SLauncher



class SMAutoLauncher(AutoLauncher):
    """
    AutoLauncher object for Sagemaker
    """

    @staticmethod
    def get_launchers():
        """Returns supported launchers as a dictionary from launcher name to launcher class"""
        return {
            "k8s": SMK8SLauncher,
        }


class SMJobPaths(job_utils.JobPaths):
    """
    Our launcher contains an extra entry script called train_script.sh
    This class is used to specify its path
    """

    @property
    def train_script_file(self) -> Path:
        return self._folder / f"train_script.sh"


class SMK8SLauncher(K8SLauncher):
    """
    Launcher for SM training jobs using K8s.
    """

    def _make_submission_file_text(self, command_groups: List[List[str]]) -> str:
        """
        Generate the script to launch the Helm chart.
        A very simple bash script is generated which runs `helm install` for the
        Helm chart that was generated.

        :param List[List[str]] command_groups: Command groups to launch with
        :return: submission script file's text
        :rtype: str
        """
        paths = job_utils.JobPaths(folder=self.folder, job_name=self.job_name)
        helm_charts = paths.folder / "k8s_template"
        job_name = self.job_name.replace("_", "-")

        extra_helm_args = ""
        if self.parameters.get("namespace", None):
            extra_helm_args += f" --namespace {self.parameters['namespace']}"

        # Apply a timeout of 15min in case images take a long time to bring up
        # or pre-install hooks take a while
        return f"#!/bin/bash\nhelm install --timeout=15m --wait {extra_helm_args} {job_name} {helm_charts}\n"
