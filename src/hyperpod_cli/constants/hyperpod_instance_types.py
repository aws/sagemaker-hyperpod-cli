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
from enum import Enum


class HyperpodInstanceType(Enum):
    ML_P4D_24XLARGE = "ml.p4d.24xlarge"
    ML_P4DE_24XLARGE = "ml.p4de.24xlarge"
    ML_P5_48XLARGE = "ml.p5.48xlarge"
    ML_TRN1_32XLARGE = "ml.trn1.32xlarge"
    ML_TRN1N_32XLARGE = "ml.trn1n.32xlarge"
    ML_G5_XLARGE = "ml.g5.xlarge"
    ML_G5_2XLARGE = "ml.g5.2xlarge"
    ML_G5_4XLARGE = "ml.g5.4xlarge"
    ML_G5_8XLARGE = "ml.g5.8xlarge"
    ML_G5_12XLARGE = "ml.g5.12xlarge"
    ML_G5_16XLARGE = "ml.g5.16xlarge"
    ML_G5_24XLARGE = "ml.g5.24xlarge"
    ML_G5_48XLARGE = "ml.g5.48xlarge"
    ML_C5_LARGE = "ml.c5.large"
    ML_C5_XLARGE = "ml.c5.xlarge"
    ML_C5_2XLARGE = "ml.c5.2xlarge"
    ML_C5_4XLARGE = "ml.c5.4xlarge"
    ML_C5_9XLARGE = "ml.c5.9xlarge"
    ML_C5_12XLARGE = "ml.c5.12xlarge"
    ML_C5_18XLARGE = "ml.c5.18xlarge"
    ML_C5_24XLARGE = "ml.c5.24xlarge"
    ML_C5N_LARGE = "ml.c5n.large"
    ML_C5N_2XLARGE = "ml.c5n.2xlarge"
    ML_C5N_4XLARGE = "ml.c5n.4xlarge"
    ML_C5N_9XLARGE = "ml.c5n.9xlarge"
    ML_C5N_18XLARGE = "ml.c5n.18xlarge"
    ML_M5_LARGE = "ml.m5.large"
    ML_M5_XLARGE = "ml.m5.xlarge"
    ML_M5_2XLARGE = "ml.m5.2xlarge"
    ML_M5_4XLARGE = "ml.m5.4xlarge"
    ML_M5_8XLARGE = "ml.m5.8xlarge"
    ML_M5_12XLARGE = "ml.m5.12xlarge"
    ML_M5_16XLARGE = "ml.m5.16xlarge"
    ML_M5_24XLARGE = "ml.m5.24xlarge"
    ML_T3_MEDIUM = "ml.t3.medium"
    ML_T3_LARGE = "ml.t3.large"
    ML_T3_XLARGE = "ml.t3.xlarge"
    ML_T3_2XLARGE = "ml.t3.2xlarge"
