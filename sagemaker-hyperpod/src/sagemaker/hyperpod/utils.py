import re


def get_name_from_arn(arn: str) -> str:
    """
    Parse the EKS cluster name from an EKS ARN.

    Args:
        arn (str): The ARN of the EKS cluster.

    Returns: str: The name of the EKS cluster if parsing is
    successful, otherwise raise RuntimeError.
    """
    # Define the regex pattern to match the EKS ARN and capture the cluster name
    pattern = r"arn:aws:eks:[\w-]+:\d+:cluster/([\w-]+)"
    match = re.match(pattern, arn)

    if match:
        return match.group(1)
    else:
        raise RuntimeError("cannot get EKS cluster name")
