from pathlib import Path
from typing import Any, List, Union

import nemo_launcher.utils.job_utils as job_utils
from nemo_launcher.core.launchers import AutoLauncher, K8SLauncher, SlurmLauncher


class SMAutoLauncher(AutoLauncher):
    """
    AutoLauncher object for Sagemaker
    """

    @staticmethod
    def get_launchers():
        """Returns supported launchers as a dictionary from launcher name to launcher class"""
        return {
            "bcm": SMSlurmLauncher,
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


class SMSlurmLauncher(SlurmLauncher):
    """
    Launcher for SM training jobs using slurm.
    This launcher will launch the job using `torchrun`, unlike the NeMo slurm launcher which use Pytorch lightning
    to handle the torch.distributed. This launcher will create a separate train_script.sh with proper `torchrun` distributed arg prepared.
    Checking `_make_train_script_text` function in stage.py for more details.
    """

    def __init__(self, folder: Union[Path, str], job_name: str, **kwargs: Any) -> None:
        # We need to handle this ntasks_per_node specifically
        # Since we are using torchrun to launch custom jobs, we can not use ntasks_per_node in sbatch command
        self.ntasks_per_node = kwargs.pop("ntasks_per_node", 8)
        if "train_script_text" in kwargs:
            self.train_script_text = kwargs.pop("train_script_text")
        else:
            raise ValueError(f"Missing train_script_text from launcher kwargs {kwargs}")
        if "hostfile" in kwargs:
            self.hostfile = kwargs.pop("hostfile")
        else:
            raise ValueError(f"Missing hostfile from launcher kwargs {kwargs}")
        if "nodeid" in kwargs:
            self.nodeid = kwargs.pop("nodeid")
        else:
            raise ValueError(f"Missing nodeid from launcher kwargs {kwargs}")
        super().__init__(folder, job_name, **kwargs)

    def _make_train_script_file(self):
        """
        Create the custom train_script.sh
        """
        job_paths = SMJobPaths(folder=self.folder, job_name=self.job_name)
        folder = job_paths.folder
        folder.mkdir(parents=True, exist_ok=True)
        train_script_file_path = job_paths.train_script_file
        with train_script_file_path.open("w") as f:
            f.write(self.train_script_text)

    def launch(self, command_groups: List[List[str]]) -> str:
        # Create the custom train_script.sh before launching the real job
        self._make_train_script_file()
        super().launch(command_groups)

    def _make_submission_file_text(self, command_groups: List[List[str]]) -> str:
        """
        The submission file will be responsible for the following
        - Handle sbatch config (implemented in upstream)
        - Handle env variables (implemented in upstream)
        - Handle storing distribution information which will be consumed by train_script.sh
        - Call train_script.sh with proper srun command
        """
        origin_sbatch_str = super()._make_submission_file_text(command_groups)
        origin_sbatch_str = origin_sbatch_str.split("\n")
        assert origin_sbatch_str[0] == "#!/bin/bash", origin_sbatch_str[0]
        command_idx = None
        for idx, sbatch_str in enumerate(origin_sbatch_str):
            if sbatch_str.startswith("# command"):
                command_idx = idx
                break
        assert (
            command_idx is not None
        ), f"Can not find command in the submission file str: {origin_sbatch_str}"
        distributed_strs = [
            "",
            "# Prepare distributed files",
            f'srun -l bash -c "scontrol show hostnames | sort > {self.hostfile}"',
            f'srun -l bash -c "echo $SLURM_NODEID > {self.nodeid}"',
            "",
        ]
        updated_sbatch_str = (
            origin_sbatch_str[:command_idx] + distributed_strs + origin_sbatch_str[command_idx:]
        )
        return "\n".join(updated_sbatch_str)


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
