# HyperpodCLI

** Describe HyperpodCLI here **
A CLI tool to manage Kubernetes jobs with commands to submit, describe, list, cancel jobs, and more.

## Documentation

Generated documentation for the latest released version can be accessed here:
https://devcentral.amazon.com/ac/brazil/package-master/package/go/documentation?name=HyperpodCLI&interface=1.0&versionSet=live

## Development

See instructions in DEVELOPMENT.md

## Contributing and building package

[//]: # (TODO)

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

4. config.yaml and result folder already created locally. 
You can submit the jobs by running 

```
hyperpod start-job --config-file ./examples/basic-job-example-config.yaml
```
