Cluster Management
================================

.. automodule:: sagemaker.hyperpod.cluster_management.hp_cluster_stack
    :exclude-members: model_config, __init__
    :no-undoc-members:
    :no-show-inheritance:



SageMaker Core Cluster Update Method
====================================

The cluster management also supports updating cluster properties using the SageMaker Core Cluster update method from ``sagemaker_core.main.resources``:

.. py:method:: Cluster.update(instance_groups=None, restricted_instance_groups=None, node_recovery=None, instance_groups_to_delete=None)

   Update a SageMaker Core Cluster resource.

   **Parameters:**

   .. list-table::
      :header-rows: 1
      :widths: 25 20 55

      * - Parameter
        - Type
        - Description
      * - instance_groups
        - List[ClusterInstanceGroupSpecification]
        - List of instance group specifications to update
      * - restricted_instance_groups
        - List[ClusterRestrictedInstanceGroupSpecification]
        - List of restricted instance group specifications
      * - node_recovery
        - str
        - Node recovery setting ("Automatic" or "None")
      * - instance_groups_to_delete
        - List[str]
        - List of instance group names to delete

   **Returns:** 
   
   The updated Cluster resource

   **Raises:**
   
   - ``botocore.exceptions.ClientError``: AWS service related errors
   - ``ConflictException``: Conflict when modifying SageMaker entity
   - ``ResourceLimitExceeded``: SageMaker resource limit exceeded
   - ``ResourceNotFound``: Resource being accessed is not found
   

   .. dropdown:: Usage Examples
      :open:

      .. code-block:: python

         from sagemaker_core.main.resources import Cluster
         from sagemaker_core.main.shapes import ClusterInstanceGroupSpecification
         
         # Get existing cluster
         cluster = Cluster.get(cluster_name="my-cluster")
         
         # Update cluster with new instance groups and node recovery
         cluster.update(
             instance_groups=[
                 ClusterInstanceGroupSpecification(
                     InstanceCount=2,
                     InstanceGroupName="worker-nodes",
                     InstanceType="ml.m5.large"
                 )
             ],
             node_recovery="Automatic",
             instance_groups_to_delete=["old-group-name"]
         )