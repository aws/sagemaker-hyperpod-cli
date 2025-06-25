#!/bin/bash

SRC_DIR="HyperPodHelmChart"
OUTPUT_DIR="HyperPodHelmChartForRIG"
TRAINING_OPERATORS=dependencies-training-operators # dependencies- prefix from standard Helm installation

# Format: "<eks|hyperpod>,namespace,<k8s_name|chart_dir>"
add_ons=(
    "eks,kube-system,aws-node,daemonset"
    "eks,kube-system,coredns,deployment"
    #"hp,kube-system,mpi-operator,deployment"
    #"hp,kube-system,neuron-device-plugin,daemonset"
    "hp,kubeflow,$TRAINING_OPERATORS,deployment"
)

generate_helm_chart_root() {
    local outdir=$1
    local name=$2
    cat << EOF > $OUTPUT_DIR/charts/$name/Chart.yaml
apiVersion: v2
name: $name
version: 0.1.0
appVersion: 1.0
description: A Helm chart for setting up $name in RIG Workers
EOF
}

get_helm_chart_from_eks() {
    local k=$1
    local d=$2
    local ns=$3
    if [ "$k" = "daemonset" ]; then
        kubectl get daemonset $d -n $ns -o yaml
    else
        kubectl get deployment $d -n $ns -o yaml
    fi
}

get_helm_chart_from_local() {
    local srcdir=$1
    local chart=$2
    local kind=$3

    # Deal with Casing
    local k="Deployment"
    if [ "$kind" = "daemonset" ]; then
        k="DaemonSet"
    fi

    helm template dependencies $srcdir/charts/$chart -f $srcdir/values.yaml -f $srcdir/charts/$chart/values.yaml --debug | \
        yq "select(.kind == \"$k\")" -
}

enable_nodeselectors_and_tolerations_overrides() {
    local outpath=$1
    yq e "
        .metadata.name = \"rig-\" + .metadata.name |
        del(.status) |
        .spec.template.spec.nodeSelector = \"NODESELECTORS\" |
        .spec.template.spec.tolerations = \"TOLERATIONS\"
    " - | \
        sed "s/NODESELECTORS/\n{{ toYaml (index .Values \"nodeSelector\") | indent 8 }}/" |
        sed "s/TOLERATIONS/\n{{ toYaml (index .Values \"tolerations\"  ) | indent 8 }}/" > $outpath
}

override_image_if_below_version() {
    local IMAGE=$1
    local MIN_VERSION=$2
    local MIN_VERSION_TAG=$3
    local CONTAINER_TYPE=${4:-containers}

    local override=$(cat)
    local uri=$(echo "$override" | yq e ".spec.template.spec.${CONTAINER_TYPE}[] | select(.name == \"$IMAGE\").image" -)
    local version=$(echo $uri | cut -d':' -f2 | cut -d'-' -f1 | tr -d 'v')
    local repo=$(echo $uri | cut -d':' -f1)
 
    if test "$(echo -e "$version\n$MIN_VERSION" | sort -V | head -n 1)" != "$MIN_VERSION"; then
        override=$(echo "$override" | \
            yq e -P ".spec.template.spec.${CONTAINER_TYPE}[] |= select(.name == \"$IMAGE\").image = \"$repo:$MIN_VERSION_TAG\"" -)
    fi
    echo "$override"
}

override_aws_node() {
    ###################################################
    # aws-node has special requirements as of 6/6/2025
    #  1. For non-RIG Daemonset
    #     1. Need to append new nodeAffinity rules to NOT deploy to RIG nodes
    #  2. For RIG Daemonset
    #     1. Need to override the container images
    #     2. Need to append new environment variable ENABLE_IMDS_ONLY_MODE
    #     3. Need to override existing environment variable ENABLE_PREFIX_DELEGATION
    #     4. Need to append new nodeAffinity rules to only deploy to RIG nodes
    ####################################################
    
    local outdir="$1"                # Daemonset will be in separate files
    local tmp="$outpath.tmp.yaml"    # Temporary space to work on overrides
    cat > $tmp                       # Save the YAML from EKS so we can override it

    ################################################
    # 1 - Non-RIG Daemonset updates
    ################################################
    yq e "
        .spec.template.spec.affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms[] |=
		.matchExpressions += [{\"key\":\"sagemaker.amazonaws.com/instance-group-type\",\"operator\":\"NotIn\",\"values\":[\"Restricted\"]}] |
		del(.status)
    " $tmp > $outdir/daemonset.nonrig.yaml

    ################################################
    # 2 - RIG Daemonset updates
    ################################################
    rig_nodes_only=$(yq e -P "
        .spec.template.spec.affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms[] |=
		.matchExpressions += [{\"key\":\"sagemaker.amazonaws.com/instance-group-type\",\"operator\":\"In\",\"values\":[\"Restricted\"]}]
    " $tmp)
    set_and_append_envvars=$(echo "$rig_nodes_only" | \
	    yq e -P "
		.spec.template.spec.containers[] |= 
		    select(.name == \"aws-node\").env[] |= 
		    select(.name == \"ENABLE_PREFIX_DELEGATION\").value = \"true\" |
	        .spec.template.spec.containers[] |=
		    select(.name == \"aws-node\").env += [{\"name\": \"ENABLE_IMDS_ONLY_MODE\", \"value\": \"true\"}]
	    " - )

    override_images="$set_and_append_envvars"
    override_images=$(echo "$override_images" | override_image_if_below_version aws-node 1.19.6 "v1.19.6-eksbuild.1" )
    override_images=$(echo "$override_images" | override_image_if_below_version aws-eks-nodeagent 1.2.2 "v1.2.2-eksbuild.1" )
    override_images=$(echo "$override_images" | override_image_if_below_version aws-vpc-cni-init 1.19.6 "v1.19.6-eksbuild.1" initContainers)

    change_metadata=$(echo "$override_images" | \
	    yq e -P "
                .metadata.name = \"rig-\" + .metadata.name |
                .metadata.annotations.[\"helm.sh/hook-weight\"] = \"-1\" |
		del(.status)
            " - )

    echo "$change_metadata" | yq eval -P '.' - > $outdir/daemonset.rig.yaml

    rm $tmp
}

override_coredns() {
    ###################################################
    # coredns has special requirements as of 6/6/2025
    #  1. Need to convert the Deployment template into a Daemonset template
    ####################################################
    
    local outdir="$1"                # Daemonset will be in separate files
    local tmp="$outpath.tmp.yaml"    # Temporary space to work on overrides
    cat > $tmp                       # Save the YAML from EKS so we can override it

    ################################################
    # 1 - Convert to Daemonset
    ################################################
    yq e "
        .kind = \"DaemonSet\" |
        .metadata.name = \"rig-\" + .metadata.name |
        .metadata.annotations.[\"helm.sh/hook-weight\"] = \"0\" |
        .spec.template.spec.nodeSelector = {\"sagemaker.amazonaws.com/instance-group-type\": \"Restricted\"} |
        .spec.template.spec.tolerations += [{
            \"key\": \"sagemaker.amazonaws.com/RestrictedNode\",
            \"operator\": \"Equal\",
            \"value\": \"Worker\",
            \"effect\": \"NoSchedule\"
        }] |
        del(.status) |
        del(.spec.replicas) |
        del(.spec.progressDeadlineSeconds) |
        del(.spec.revisionHistoryLimit) |
        del(.spec.template.spec.topologySpreadConstraints) |
	.spec.updateStrategy = {
            \"type\": .spec.strategy.type,
            \"rollingUpdate\": {
                \"maxUnavailable\": 1
            }
        } |
        del(.spec.strategy)
    " $tmp > $outdir/daemonset.rig.yaml

    rm $tmp
}

override_training_operators() {
    #####################################################
    # training-operators dependency needs to be present
    # to schedule pytorch jobs but by by default, only
    # tolerates non-RIG nodes
    #
    # Therefore, needs to tolerate RIG node taint, 
    # but still prefer scheduling onto non-RIG
    # in case cluster consists of both non-RIG and RIG
    #
    # NOTE: this based on the original Helm installation
    #       of training-operators Deployment.
    #       There are no affinities nor tolerations
    #       as of commit 
    #       https://github.com/aws/sagemaker-hyperpod-cli/blob/9ff002f949bc408849f7673678f46a3326983ed2/helm_chart/HyperPodHelmChart/charts/training-operators/templates/Deployment/training-operator-kubeflow-Deployment.yaml
    #####################################################
   
    # Using kubectl directly since relatively simple patch 
    # that does not require new separeate file/deployments specific for RIG
    kubectl patch deployment $TRAINING_OPERATORS -n kubeflow --type=json -p='[
      {
        "op": "add",
        "path": "/spec/template/spec/tolerations",
        "value": [
          {
            "key": "sagemaker.amazonaws.com/RestrictedNode",
            "value": "Worker",
            "effect": "NoSchedule"
          }
        ]
      },
      {
        "op": "add",
        "path": "/spec/template/spec/affinity",
        "value": {
          "nodeAffinity": {
            "preferredDuringSchedulingIgnoredDuringExecution": [
              {
                "weight": 100,
                "preference": {
                  "matchExpressions": [
                    {
                      "key": "sagemaker.amazonaws.com/instance-group-type",
                      "operator": "NotIn",
                      "values": ["Restricted"]
                    }
                  ]
                }
              }
            ]
          }
        }
      }
    ]'
}

fetch_yaml_and_enable_overrides() {
    local resources=("${!1}")
    
    rm -rf $OUTPUT_DIR/charts
    
    for resource in "${resources[@]}"; do
        IFS=',' read -r scope namespace name kind <<< "$resource"
	echo "Processing $scope add-on called $name in namespace $namespace..."
        
	value_safe_name=${name//-/_} # Convert hyphens to underscores

        #####################################################
        # Clean and (Re)Create Helm chart directories
        #####################################################
	if [ "$name" != "$TRAINING_OPERATORS" ]; then
            rm -rf $OUTPUT_DIR/charts/$name/templates
            rm -f $OUTPUT_DIR/charts/$name/*.tgz
            mkdir -p $OUTPUT_DIR/charts/$name/templates
	fi

        #####################################################
        # Enable Overrides in Helm Charts/YAML
        #####################################################
	local helm_chart=""
        local outpath="$OUTPUT_DIR/charts/$name/templates/rig.$name.yml"
	if [ "$scope" = "eks" ]; then
            generate_helm_chart_root $OUTPUT_DIR $name
            if [ "$name" = "aws-node" ]; then
                # aws-node is a special case with different requirements
                get_helm_chart_from_eks $kind $name $namespace | \
		    override_aws_node $(dirname $outpath)
	    elif [ "$name" = "coredns" ]; then
		# corens is a special case with different requirements for multi-RIG
		get_helm_chart_from_eks $kind $name $namespace | \
		    override_coredns $(dirname $outpath)
	    else 
		get_helm_chart_from_eks $kind $name $namespace | \
		    enable_nodeselectors_and_tolerations_overrides $outpath
            fi
	else
	    if [ "$name" = "$TRAINING_OPERATORS" ]; then
		# training-operators is a special case with different requirements
		continue
            else
                cp -r $SRC_DIR/charts/$name/. $OUTPUT_DIR/charts/$name
                rm -rf $OUTPUT_DIR/charts/$name/templates/*

                get_helm_chart_from_local $SRC_DIR $name $kind | \
                   enable_nodeselectors_and_tolerations_overrides $outpath
	    fi
	fi
    done
}

assert_addons_enabled() {
    local resources=("${!1}")
    local response=""
    for resource in "${resources[@]}"; do
        IFS=',' read -r scope namespace name kind <<< "$resource"
        response=$(kubectl get $kind $name -n $namespace --no-headers 2>&1)
        if [[ "$response" == *"Error from server (NotFound)"* ]] || [ -z "$response" ]; then
            echo "Namespace $namespace does not exist or No $kind $name found in namespace $namespace. Please ensure CNI, CoreDNS add-ons enabled, and that standard HyperPod Helm chart is installed for this cluster before installing RIG dependencies."
            exit 1
        fi
    done
}

refresh_helm_dependencies() {
    # This needs to be run after any dependency template change before "helm <template | install>"
    helm dependencies update ./HyperPodHelmChartForRIG
}

render_rig_helm_chart() {
    local outpath=$1
    helm template rig-dependencies ./HyperPodHelmChartForRIG --namespace kube-system -f ./HyperPodHelmChartForRIG/values.yaml > $outpath
    echo ""
    echo ""
    echo "Rendered target Helm chart at $outpath"
    echo ""
    echo ""
}

confirm_installation_with_user() {
    local outpath=$1
    read -p "🚀 Do you want to install this Helm chart ($outpath) ? [y/N]: " confirm

    if [[ "$confirm" =~ ^[Yy]$ ]]; then
      echo "🔧 Installing Helm chart..."
      helm upgrade --install rig-dependencies ./HyperPodHelmChartForRIG --namespace kube-system -f ./HyperPodHelmChartForRIG/values.yaml
      if [ $? -ne 0 ]; then
        echo "RIG Helm Installation Failed. Exiting (0/3 steps completed)..."
        return 1
      fi
  
      # aws-node needs specific instllation for *.nonrig.yaml
      kubectl apply -f HyperPodHelmChartForRIG/charts/aws-node/templates/daemonset.nonrig.yaml -n kube-system
      if [ $? -ne 0 ]; then
        echo "RIG Helm Installation Failed (aws-node). Exiting (only 1/3 steps completed)..."
        return 1
      fi

      # training-operator needs specific patch
      override_training_operators
      if [ $? -ne 0 ]; then
        echo "RIG Helm Installation Failed (training-operator). Exiting (only 2/3 steps completed)..."
        return 1
      fi

      echo ""
      echo "RIG Helm Installation Succeeded (3/3 steps completed)."
      echo ""

      # Warn user about CNI start up
      echo ""
      echo "⚠️ Note: aws-node (AWS VPC CNI) is a critical add-on for general pod use."
      echo "Other pods that depend on aws-node (e.g. CoreDNS, HyperPod HealthMonitoringAgent,...) may experience 'FailedCreatePodSandBox' if the aws-node pods are not available before start up."
      echo "Therefore, please allow additional time for K8s to recreate the pods and/or manually recreate the pods (or let K8s recreate after cleaning up) before full cluster use."
      echo ""
    else
      echo "❌ Installation cancelled."
    fi
}

ensure_yq_installed(){
    if ! command -v yq &> /dev/null; then
        echo "Error: yq is required but not installed. Please install version >= 4 (e.g. https://github.com/mikefarah/yq/releases/tag/v4)"
        exit 1
    fi

    version=$(yq --version | grep -o 'v[0-9]\+' | cut -d 'v' -f 2 )
    if [ "$version" -lt "4" ]; then
        echo "Error: yq version 4 or higher is required (e.g. https://github.com/mikefarah/yq/releases/tag/v4)"
        echo "Current version: $(yq -q --version)"
        echo "Please upgrade yq"
        exit 1
    fi
}

main() {
    ensure_yq_installed

    assert_addons_enabled add_ons[@]
    
    set -e
    fetch_yaml_and_enable_overrides add_ons[@]

    local outpath="./rig-dependencies.yaml"
    refresh_helm_dependencies
    render_rig_helm_chart $outpath
    confirm_installation_with_user $outpath
}

main
