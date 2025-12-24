# Submitting a PyTorch Training Job - HyperPod CLI End-to-End Walkthrough

This example shows how to fine-tune a **Qwen3 4B Thinking** model using PyTorch FSDP and QLora on your HyperPod cluster.

In the following you will:
- Create a sample dataset for training and upload it to Amazon S3.
- Upload the training script and it's configuration to Amazon S3.
- Create a training docker image and push it to Amazon ECR.
- Submit the job to your cluster using the CLI and monitor it's progress.

This example assumes that you completed the setup instructions in [00-getting-started/00-setup.md](../00-getting-started/00-setup.md).

## Training Dataset

To create the training dataset for this example, please run the following script,
which will download and pre-process the [`interstellarninja/hermes_reasoning_tool_use`](https://huggingface.co/datasets/interstellarninja/hermes_reasoning_tool_use) dataset
to the current local directory under `./data/`.
```bash
pip install -r ./scripts/requirements.txt
python ./scripts/create-training-dataset.py
```

Lastly, upload the dataset to the Amazon S3 bucket, which is connected to your HyperPod cluster's FSx for Lustre Filesystem
through DRA.
```bash
S3_BUCKET_NAME="PLEASE_FILL_IN"
S3_PREFIX="qwen-cli-example"
S3_PATH="s3://$S3_BUCKET_NAME/$S3_PREFIX"

aws s3 sync ./data/ $S3_PATH/dataset
```

Verify that the upload was successful by running:
```bash
aws s3 ls $S3_PATH --recursive
```

## Training Script and Configuration
The training script is already pre-configured with default values in `./training_scripts/args.yaml`
which you do not need to adapt. 

You can optionally add configurations for **MLFlow tracking**. To utilize MLFlow tracking, open `./training_scripts/args.yaml`
in an editor, e.g. `vscode`, and configure the following two fields:
```yaml
mlflow_uri: "" # MLflow tracking server URI
mlflow_experiment_name: "" # MLflow experiment name
```

Upload the training script and configuration to S3 using the following command:
```bash
aws s3 sync ./training_scripts/ $S3_PATH/scripts/
```

## Training Docker Image

The example uses the `pytorch-training:2.8.0-gpu-py312-cu129-ubuntu22.04-ec2` docker image,
provided by AWS as a base image. This example provides a Dockerfile that extends this image
with the specific requirements of the training job, the training python script as well as the HyperPod Elastic Agent.

Please note that the docker images are multiple gigabytes in size, thus the following process will take some time depending on your network speed. Alternatively, this can be executed in an EC2 instance or SageMaker AI Studio instance.

Create a new ECR if required and login to it.
```bash
AWS_REGION="PLEASE_FILL_IN"
AWS_ACCOUNT_ID="PLEASE_FILL_IN"

DOCKER_IMAGE_TAG="pytorch2.8-cu129"
ECR_NAME="qwen3-finetuning"

ECR_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_NAME

aws ecr create-repository --repository-name $ECR_NAME --region $AWS_REGION 2>&1 | grep -v "RepositoryAlreadyExistsException" || echo "Repository already exists or created successfully"

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 763104351884.dkr.ecr.us-west-2.amazonaws.com
```

Build the image and push it to ECR:
```bash
cd docker

docker build --platform linux/amd64 -t $ECR_URI:$DOCKER_IMAGE_TAG .
docker push $ECR_URI:$DOCKER_IMAGE_TAG

cd ..
```

## Submit and monitor the training job (💻)

You can submit the job to your HyperPod cluster by running the following CLI command. This example
assumes that your cluster is configured with at least 2 `ml.g5.12xlarge` instances. Please adapt the command accordingly
if you are using different instances.
```bash
JOB_NAME=qwen3-4b-thinking-2507-fsdp

hyp create hyp-pytorch-job \
    --job-name $JOB_NAME \
    --image $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_NAME:$DOCKER_IMAGE_TAG \
    --command "[hyperpodrun, --nnodes=2:2, --nproc_per_node=4, /data/$S3_PREFIX/scripts/train.py]" \
    --args "[--config, /data/$S3_PREFIX/scripts/args.yaml]" \
    --environment '{"LOGLEVEL": "INFO", "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True", "NCCL_DEBUG": "INFO", "NCCL_SOCKET_IFNAME": "^lo", "TORCH_NCCL_ASYNC_ERROR_HANDLING": "1", "FI_PROVIDER": "efa", "FI_EFA_FORK_SAFE": "1", "NCCL_PROTO": "simple"}' \
    --pull-policy "IfNotPresent" \
    --instance-type "ml.g5.12xlarge" \
    --node-count 2 \
    --tasks-per-node 4 \
    --deep-health-check-passed-nodes-only false \
    --max-retry 100 \
    --volume name=shmem,type=hostPath,mount_path=/dev/shm,path=/dev/shm,read_only=false \
    --volume name=local,type=hostPath,mount_path=/local,path=/mnt/k8s-disks/0,read_only=false \
    --volume name=fsx-volume,type=pvc,mount_path=/data,claim_name=fsx-claim,read_only=false \
    --namespace default
```

After the job got submitted successfully, you can list the jobs running on the cluster and monitor their status 
using the following command:
```bash
hyp list hyp-pytorch-job
```

Describe the job details by running:
```bash
hyp describe hyp-pytorch-job --job-name $JOB_NAME
```

List the pods of the job by running:
```bash
hyp list-pods hyp-pytorch-job --job-name $JOB_NAME
```

Get the logs for the job, from a specific pod:
```bash
hyp get-logs hyp-pytorch-job --job-name $JOB_NAME --pod-name $JOB_NAME-pod-0
```

Cancel and delete the job to free up the cluster resources by running:
```bash
hyp delete hyp-pytorch-job --job-name $JOB_NAME
```

## (Optional) Submit the training job by creating a customizable template (💻)

Alternatively to creating a training job via the `hyp create hyp-pytorch-job` command
above, the HyperPod CLI also enables a configuration file-based workflow that allows
for easy reproducability as well as further customization options as the Kubernetes
manifest template is directly exposed to the user.

Initialize a HyperPod pytorch training job configuration in a new directory by running:
```bash
mkdir pytorch-job-config && cd pytorch-job-config

hyp init hyp-pytorch-job
```

This will create three files in the new directory:
- `k8s.jinja` - Kubernetes template for a `HyperPodPyTorchJob` resource
- `config.yaml` - Configuration file that contains the values for the Kubernetes template
- `README.md` - Usage instructions for this functionality

The configuration parameters can be either modified directly in the `config.yaml` or via 
the CLI by executing `hyp configure --<parameter-name> <parameter-value>` which provides
additional validation.

To reproduce the earlier training job example, run the following commands:
```bash
hyp configure --job-name $JOB_NAME
hyp configure --image $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_NAME:$DOCKER_IMAGE_TAG
hyp configure --command "[hyperpodrun, --nnodes=2:2, --nproc_per_node=4, /data/$S3_PREFIX/scripts/train.py]"
hyp configure --args "[--config, /data/$S3_PREFIX/scripts/args.yaml]"
hyp configure --environment '{"LOGLEVEL": "INFO", "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True", "NCCL_DEBUG": "INFO", "NCCL_SOCKET_IFNAME": "^lo", "TORCH_NCCL_ASYNC_ERROR_HANDLING": "1", "FI_PROVIDER": "efa", "FI_EFA_FORK_SAFE": "1", "NCCL_PROTO": "simple"}'
hyp configure --pull-policy IfNotPresent
hyp configure --instance-type ml.g5.12xlarge
hyp configure --node-count 2
hyp configure --tasks-per-node 4
hyp configure --deep-health-check-passed-nodes-only false
hyp configure --max-retry 100
hyp configure --volume '[{"name":"shmem","type":"hostPath","mount_path":"/dev/shm","path":"/dev/shm","read_only":false},{"name":"local","type":"hostPath","mount_path":"/local","path":"/mnt/k8s-disks/0","read_only":false},{"name":"fsx-volume","type":"pvc","mount_path":"/data","claim_name":"fsx-claim","read_only":false}]'
hyp configure --namespace default
```

If specific Kubernetes entities or configuration entries need to be set that are not supported as CLI arguments,
the template in `k8s.jinja` can be modified in addition. This can be useful if you for example require additional label definitions in `metadata:` or other settings to comply with enterprise policies.

View the following files in an editor of your choice to see the configuration before submitting:
```
./k8s.jinja
./config.yaml
```

Validate the values in `config.yaml` by running:
```bash
hyp validate
```

Submit the job to the cluster by running:
```bash
hyp create
```

The final, submitted Kubernetes manifest will be stored for reference in `./run/<timestamp>/k8s.yaml` which you can again view in your favorite editor.

## (Optional) Simulate an instance failure (💻)

To validate HyperPod’s fault-tolerance behavior, you can emulate an instance reboot
(e.g., due to a GPU failure) by marking one of the nodes in your cluster as
`UnschedulablePendingReboot`. This will trigger HyperPod to detect the fault and,
if a spare instance is available, restart the job on a healthy node.

Run the following command to see the pods that are part of the current training job and the node that they are running on:
```bash
kubectl get pods -o wide 
```

This will output something similar to the following:
```bash
NAME                                READY   STATUS    RESTARTS   AGE     IP             NODE                        
qwen3-4b-thinking-2507-fsdp-pod-0   1/1     Running   0          3m53s   10.4.224.228   hyperpod-i-00b865d0114cabc20
qwen3-4b-thinking-2507-fsdp-pod-1   1/1     Running   0          3m53s   10.4.142.65    hyperpod-i-0974a98e3fc0da67b
```

Mark a node as pending reboot:
```bash
NODE=hyperpod-i-00b865d0114cabc20 # Replace this with one of your worker node IDs

kubectl label node "$NODE" \
  sagemaker.amazonaws.com/node-health-status=UnschedulablePendingReboot \
  --overwrite=true
```

Check the pod and node status again. The pod on the faulty node will restarted on the spare node:
```bash
kubectl get pods -o wide 
```

Describe the job to verify that the fault has been detected and that recovery is in progress:
```
hyp describe hyp-pytorch-job --job-name $JOB_NAME
```

Optionally, run a command inside one of the job’s pods (for example, to inspect GPU state):
```
hyp exec hyp-pytorch-job --job-name $JOB_NAME --pod $JOB_NAME-pod-0 -- nvidia-smi
```

Lastly, cancel and delete the job to free up the cluster resources by running:
```bash
hyp delete hyp-pytorch-job --job-name $JOB_NAME
```
