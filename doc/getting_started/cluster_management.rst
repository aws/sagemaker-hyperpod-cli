Cluster Management
===============================================

This guide will help you create and manage your first HyperPod cluster using the CLI.

Prerequisites
-------------

Before you begin, ensure you have:

- An AWS account with appropriate permissions for SageMaker HyperPod
- AWS CLI configured with your credentials
- HyperPod CLI installed (``pip install sagemaker-hyperpod``)

.. note::
   **Region Configuration**: For commands that accept the ``--region`` option, if no region is explicitly provided, the command will use the default region from your AWS credentials configuration.

Creating Your First Cluster
----------------------------

1. Start with a Clean Directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's recommended to start with a new and clean directory for each cluster configuration:

.. code-block:: bash

   mkdir my-hyperpod-cluster
   cd my-hyperpod-cluster

2. Initialize a New Cluster Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. tab-set::

   .. tab-item:: CLI

      .. code-block:: bash

         hyp init hyp-cluster

This creates three files:

- ``config.yaml``: The main configuration file you'll use to customize your cluster
- ``cfn_params.jinja``: A reference template for CloudFormation parameters
- ``README.md``: Usage guide with instructions and examples

.. important::
   The ``resource_name_prefix`` parameter in the generated ``config.yaml`` file serves as the primary identifier for all AWS resources created during deployment. Each deployment must use a unique resource name prefix to avoid conflicts. This prefix is automatically appended with a unique identifier during cluster creation to ensure resource uniqueness.

3. Configure Your Cluster
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can configure your cluster in two ways:

**Option 1: Edit config.yaml directly**

The config.yaml file contains key parameters like:

.. code-block:: yaml

   template: hyp-cluster
   namespace: kube-system
   stage: gamma
   resource_name_prefix: sagemaker-hyperpod-eks

**Option 2: Use CLI/SDK commands**

.. tab-set::

   .. tab-item:: CLI

      .. code-block:: bash

         hyp configure --resource-name-prefix your-resource-prefix   

4. Create the Cluster
~~~~~~~~~~~~~~~~~~~~~

.. tab-set::

   .. tab-item:: CLI

      .. code-block:: bash

         hyp create --region your-region

This will:

- Validate your configuration
- Create a timestamped folder in the ``run`` directory
- Initialize the cluster creation process

5. Monitor Your Cluster
~~~~~~~~~~~~~~~~~~~~~~~

Check the status of your cluster:

.. tab-set::

   .. tab-item:: CLI

      .. code-block:: bash

         hyp describe hyp-cluster your-cluster-name --region your-region

   .. tab-item:: SDK

      .. code-block:: python
         
         from sagemaker.hyperpod.cluster_management.hp_cluster_stack import HpClusterStack

         # Describe a specific cluster stack
         response = HpClusterStack.describe("your-cluster-name", region="your-region")
         print(f"Stack Status: {response['Stacks'][0]['StackStatus']}")
         print(f"Stack Name: {response['Stacks'][0]['StackName']}")
         

List all clusters:

.. tab-set::

   .. tab-item:: CLI

      .. code-block:: bash

         hyp list hyp-cluster --region your-region

   .. tab-item:: SDK

      .. code-block:: python

         from sagemaker.hyperpod.cluster_management.hp_cluster_stack import HpClusterStack

         # List all CloudFormation stacks (including cluster stacks)
         stacks = HpClusterStack.list(region="your-region")
         for stack in stacks['StackSummaries']:
            print(f"Stack: {stack['StackName']}, Status: {stack['StackStatus']}")


Common Operations
-----------------

Update a Cluster
~~~~~~~~~~~~~~~~~

.. tab-set::

   .. tab-item:: CLI

      .. code-block:: bash

         hyp update hyp-cluster \
             --cluster-name your-cluster-name \
             --instance-groups "[]" \
             --region your-region   

Reset Configuration
~~~~~~~~~~~~~~~~~~~

.. tab-set::

   .. tab-item:: CLI

      .. code-block:: bash

         hyp reset


Best Practices
--------------

- Always validate your configuration before submission:

  .. tab-set::

     .. tab-item:: CLI

        .. code-block:: bash

           hyp validate

  .. note::
     This command performs **syntactic validation only** of the ``config.yaml`` file against the appropriate schema. It checks:

     - **YAML syntax**: Ensures file is valid YAML
     - **Required fields**: Verifies all mandatory fields are present
     - **Data types**: Confirms field values match expected types (string, number, boolean, array)
     - **Schema structure**: Validates against the template's defined structure

     This command performs syntactic validation only and does **not** verify the actual validity of values (e.g., whether AWS regions exist, instance types are available, or resources can be created).
     
- Use meaningful resource prefixes to easily identify your clusters
- Monitor cluster status regularly after creation
- Keep your configuration files in version control for reproducibility

Next Steps
----------

After creating your cluster, you can:

- Connect to your cluster:

  .. tab-set::

     .. tab-item:: CLI

        .. code-block:: bash

           hyp set-cluster-context --cluster-name your-cluster-name

- Start training jobs with PyTorch
- Deploy inference endpoints
- Monitor cluster resources and performance

For more detailed information on specific commands, use the ``--help`` flag:

.. code-block:: bash

   hyp <command> --help