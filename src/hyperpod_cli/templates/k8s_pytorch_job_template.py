KUBERNETES_PYTORCH_JOB_TEMPLATE = """### Please keep template file unchanged ###
defaults:
    - override hydra/job_logging: stdout

hydra:
    run:
        dir: .
    output_subdir: null

training_cfg:
    entry_script: ??? # Path to the entry script of training/fine-tuning. This path should be inside container or relative path in git repo
    script_args: ??? # Entry script arguments
    run:
        nodes: ??? # Number of nodes to use for current training
        ntasks_per_node: ??? # Number of tasks per node
cluster:
    cluster_type: k8s  # currently k8s only
    instance_type: ???
    cluster_config:
        namespace: ??? # the namespace to submit job
        custom_labels: ???
        service_account_name: ???
        annotations: ???
        priority_class_name: ???
        # Create k8s NodeAffinity to select nodes to deploy jobs which matches required and preferred labels
        # Structure:
        #   label_selector:
        #     required: <required label key-values pair>
        #     preferred: <preferred label key-values pair>
        #     weights: <weights list used by preferred labels to get nodes priority>
        # Example:
        #   label_selector:
        #     required:
        #       example-label-key:
        #         - expected-label-value-1
        #         - expected-label-value-2
        #     preferred:
        #       preferred-label-key:
        #         - preferred-label-value-1
        #         - preferred-label-value-2
        #     weights:
        #       - 100
        label_selector: ???
        # persistent volume, usually used to mount FSx
        persistent_volume_claims: ???
        pullPolicy: ??? # policy to pull container, can be Always, IfNotPresent and Never
        restartPolicy: ??? # PyTorchJob restart policy

base_results_dir: ???  # Location to store the results, checkpoints and logs.
container_mounts: # List of additional paths to mount to container. They will be mounted to same path.
    - null
container: ??? # container to use

env_vars:
    NCCL_DEBUG: INFO # Logging level for NCCL. Set to "INFO" for debug information
"""
