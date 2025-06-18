import unittest
import pytest
from sagemaker.hyperpod.utils import get_eks_name_from_arn


class TestUtils(unittest.TestCase):
    def test_get_name_from_arn_valid(self):
        # Test with valid ARN
        arn = "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"
        result = get_eks_name_from_arn(arn)
        self.assertEqual(result, "my-cluster")

        # Test with different region and account
        arn = "arn:aws:eks:eu-central-1:987654321098:cluster/test-cluster"
        result = get_eks_name_from_arn(arn)
        self.assertEqual(result, "test-cluster")

        # Test with hyphenated cluster name
        arn = "arn:aws:eks:us-east-1:123456789012:cluster/my-hyperpod-cluster"
        result = get_eks_name_from_arn(arn)
        self.assertEqual(result, "my-hyperpod-cluster")

