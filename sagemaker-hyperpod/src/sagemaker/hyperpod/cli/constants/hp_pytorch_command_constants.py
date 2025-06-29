HELP_TEXT = """
HyperPod PyTorch Job CLI
Find more information at: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod.html
Commands:
  * create         Create and submit a PyTorch training job
                   Using either config file or command line parameters

Examples:
  
  Create and submit job:
    hp hp-pytorch-job create --job-name "my_pytorch_job"  --image "my_image"

Usage:
  hp create hp-pytorch-job [options]
Use "hp create hp-pytorch-job --help" for more information about the command.
"""