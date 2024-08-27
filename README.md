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

2. Install all dependencies and built ```hyperpod``` CLI

```
pip install .
```

3. Install ```helm```

This is because SagemakerTrainingLauncher depends on Nemo submodule and Nemo use Helm to submit jobs.

```
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh
rm -f ./get_helm.sh  
```

4. config.yaml and result folder already created locally. 
You can submit the jobs by running 

```
hyperpod submit-job --config-name config.yaml
```

## Run Unit tests with coverage report without Brazil
Ensure ```pytest``` and ```pytest-cov``` is installed in the current Python environment.
Run ```pytest``` directly, and it will look ```setup.cfg``` for extra arguments which include
coverage config.

## Troubleshooting
### pytest 'start_job' related Unit Test failures
- Underlying, the Click CLIRunner unit test tool has some issue with UTF-8 encoding
- To resolve this, temporary use ```LC_ALL=C pytest test/unit_tests``` to complete the Unit tests

### pytest 'NoSuchModule' errors
- double check whether ```pytest``` is running the same venv or global environment as your project by ```which pytest```.
- If ```pytest``` is running in venv, ensure ```hyperpod``` is installed in venv.
- Otherwise, if ```pytest``` is running globally, ensure ```hyperpod``` is installed globally.

### Unit test in IDEA
Check ```setup.cfg``` and comment out line 95 to make ```pytest``` not checking ```setup.cfg``` for extra arguments.
This will make local IDEA unit tests working.
