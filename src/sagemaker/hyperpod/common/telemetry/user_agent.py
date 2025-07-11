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
"""Placeholder docstring"""

from __future__ import absolute_import

import importlib.metadata


CLI_PREFIX = "AWS-SageMaker-Hyperpod-CLI"


def get_user_agent_extra_suffix():
    """Get the user agent extra suffix string specific to SageMaker Hyperpod CLI

    Adhers to new boto recommended User-Agent 2.0 header format

    Returns:
        str: The user agent extra suffix string to be appended
    """
    suffix = "cli/{}#{}".format(
        CLI_PREFIX,
        importlib.metadata.version("sagemaker-hyperpod"),
    )

    return suffix
