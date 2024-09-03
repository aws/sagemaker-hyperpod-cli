# HyperpodCLI

** Describe HyperpodCLI here **
A CLI tool to manage Kubernetes jobs in AWS HyperPod cluster with commands to submit, describe, list, cancel jobs, and more 


## Installation

** Prerequisites **

1. Make sure your local python version >= 3.8. Supported python versions are 3.8, 3.9, 3.10, 3.11

2. Install ```helm```

SageMaker Hyperpod CLI use Helm to start Training jobs.

See ```Helm installation guide```: https://helm.sh/docs/intro/install/

```
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh
rm -f ./get_helm.sh  
```

3. Install all dependencies and built ```hyperpod``` CLI

```
pip install .
```

4. HyperPod CLI currently only supports starting kubeflow/PyTorchJob. To start a job, you need to install Kubeflow Training Operator first. 
- You can either follow [kubeflow public doc](https://www.kubeflow.org/docs/components/training/installation/) to install it.
- Or you can follow the Readme under helm_chart to install Kubeflow Training Operator.

5. config.yaml and result folder already created locally.
You can submit the jobs by running

```
hyperpod start-job --config-file ./examples/basic-job-example-config.yaml
```

## Contributing and building package

See instructions in CONTRIBUTING.md