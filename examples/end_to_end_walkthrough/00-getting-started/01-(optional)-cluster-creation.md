# Creating a HyperPod cluster using the HyperPod CLI - HyperPod CLI End-to-End Walkthrough
HyperPod clusters can generally be created using the console UI.
While this provides a convenient and user-friendly way for cluster creation,
the HyperPod CLI also provides cluster creation functionality, through a configuration
file-based, repeatable interface.

Initialize a HyperPod cluster stack configuration in a new directory by running
the following. Note that this will only create the configuration files and not yet 
start the actual cluster creation.
```
mkdir cluster-stack && cd cluster-stack

hyp init cluster-stack
```

This will create three files in the new directory:
- `cfn_params.jinja` - CloudFormation template for the HyperPod cluster stack
- `config.yaml` - Configuration file that contains the values for the CloudFormation
- `README.md` - Usage instructions for this functionality

The configuration parameters can be either modified directly in the `config.yaml` or via 
the CLI by executing `hyp configure --<parameter-name> <parameter-value>` which provides
additional validation.

For example, you can configure the stack to use a specific prefix for the names of the resources to be created
as well as a specific kubernetes version by running the following.
```
hyp configure --resource-name-prefix my-cli-cluster
hyp configure --kubernetes-version 1.33
```

Validate the values in `config.yaml` by running:
```
hyp validate
```

Finally, submit the cluster creation stack to CloudFormation by running:
```
hyp create
```

The final, submitted CloudFormation template will be stored for reference in `./run/<timestamp>/k8s.yaml`.