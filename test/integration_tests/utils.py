import subprocess
import logging
import datetime

logger = logging.getLogger(__name__)

def execute_command(command):
    """Execute a CLI command and return the result object."""
    try:
        return subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(command)}")
        logger.error(f"Return code: {e.returncode}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        raise RuntimeError(f"Failed to execute command: {' '.join(command)}. Error: {e}")

def get_time_str():
    now = datetime.datetime.now()
    return now.strftime("%m%d-%H%M%S")