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

Notes: Please run this package in cloud desktop.

1. CLI job submission depends on Kandinsky
- Install local wheel. Kandinsky package are built into a wheel under /wheels folder
- Go to your Python environment, for example PyCharm venv: ```source ~/.virtualenvs/HyperpodCLI_Py39/bin/activate```
- Pip install the wheel ```pip install wheels/launcher-0.1.0-py3-none-any.whl```
- After this, you can use ```launcher``` in CLI code and unit tests

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
### pytest failures
- double check whether ```pytest``` is running the same venv or global environment as your project by ```which pytest```.
- If ```pytest``` is running in venv, ensure ```hyperpod``` is installed in venv.
- Otherwise, if ```pytest``` is running globally, ensure ```hyperpod``` is installed globally.

### Unit test in IDEA
Check ```setup.cfg``` and comment out line 95 to make ```pytest``` not checking ```setup.cfg``` for extra arguments.
This will make local IDEA unit tests working.
