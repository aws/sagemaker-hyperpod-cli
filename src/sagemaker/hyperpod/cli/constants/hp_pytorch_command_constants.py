HELP_TEXT = """
HyperPod PyTorch Job CLI
Find more information at: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod.html
Commands:
  * create         Create and submit a PyTorch training job

  * list           List PyTorch training jobs

  * describe       Describe a PyTorch training job


Examples:

  Create and submit job:
    hyp create hp-pytorch-job  --job-name "my_pytorch_job"  --image "my_image"
  List Jobs:
    hyp list hp-pytorch-job
  Describe Job
    hyp describe hp-pytorch-job --job-name "my_pytorch_job"


Usage:
  hp create hp-pytorch-job [options]
Use "hp create hp-pytorch-job --help" for more information about the command.
Use "hp list hp-pytorch-job --help" for more information about the command.
Use "hyp describe hp-pytorch-job --help" for more information about the command.

"""
