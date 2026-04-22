import subprocess
import logging
import datetime
import time

logger = logging.getLogger(__name__)

def execute_command_with_retry(command, retries=5, delay=10):
    """Execute a CLI command with retries on failure."""
    for attempt in range(retries):
        try:
            return execute_command(command)
        except RuntimeError as e:
            if attempt < retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                time.sleep(delay)
            else:
                raise

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