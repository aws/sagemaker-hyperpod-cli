#!/bin/bash

set_script_variables() {
    # 
    # Some of this logic will be migrated into the standard Helm chart (e.g. patches)
    # For now, we will define what is needed here based on Helm Release Name lookup
    #
    RIG_HELM_RELEASE=rig-dependencies
    DATETIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    SUPPORTED_REGIONS=(
        "us-east-1"
        "eu-north-1"
    )

    SRC_DIR="HyperPodHelmChart"
    OUTPUT_DIR="HyperPodHelmChartForRIG"

    STANDARD_HELM_RELEASE_NAME=$(get_standard_hyperpod_helm_release_name)
    if [ $? -ne 0 ]; then
        exit 1
    fi
    TRAINING_OPERATORS=$STANDARD_HELM_RELEASE_NAME-training-operators
    EFA=$STANDARD_HELM_RELEASE_NAME-aws-efa-k8s-device-plugin         
    PATCH_ONLY=(
        #
        # These objects do not need entirely separate YAML; we just need to patch them to make them work with RIG
        #
        "$TRAINING_OPERATORS"
        "$EFA"
    )
    add_ons=(
        #
        # Format: "<eks|hyperpod>,namespace,<k8s_name|chart_dir>,type"
        # 
        "eks,kube-system,aws-node,daemonset"
        "eks,kube-system,coredns,deployment"
        #"hp,kube-system,mpi-operator,deployment"
        #"hp,kube-system,neuron-device-plugin,daemonset"
        "hp,kubeflow,$TRAINING_OPERATORS,deployment"
        "hp,kube-system,$EFA,daemonset"
    )
}

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

    helm template $STANDARD_HELM_RELEASE_NAME $srcdir/charts/$chart -f $srcdir/values.yaml -f $srcdir/charts/$chart/values.yaml --debug | \
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

    # We're not using `kubectl patch` for this because this expression needs to be added for each list of `matchExpressions` (there may be more than 1)
    yq e "
        .spec.template.spec.affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms[] |=
		.matchExpressions += [{\"key\":\"sagemaker.amazonaws.com/instance-group-type\",\"operator\":\"NotIn\",\"values\":[\"Restricted\"]}] |
                .metadata.annotations[\"rig.hyperpod.patch/aws-node\"] = \"{\\\"timestamp\\\":\\\" $DATETIME \\\"}\" |
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
                .metadata.annotations[\"rig.hyperpod.patch/aws-node\"] = \"{\\\"timestamp\\\":\\\" $DATETIME \\\"}\" |
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
        .metadata.annotations[\"rig.hyperpod.patch/coredns\"] = \"{\\\"timestamp\\\":\\\" $DATETIME \\\"}\" |
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
      },
      {
        "op": "add",
        "path": "/metadata/annotations/rig.hyperpod.patch~1training-operators",
        "value": "{\"timestamp\": \"'$DATETIME'\"}"
      }
    ]'
}

override_efa() {
    #####################################################
    # aws-efa-k8s-device-plugin dependency needs to be present
    # for multi-node training but by by default, only
    # tolerates non-RIG nodes
    #
    # Therefore, needs to tolerate RIG node taint.
    #
    # NOTE: this based on the original Helm installation
    #       of aws-efa-k8s-device-plugin Deployment.
    #       There are tolerations
    #       as of commit 
    #       https://github.com/aws/sagemaker-hyperpod-cli/blob/9ff002f949bc408849f7673678f46a3326983ed2/helm_chart/HyperPodHelmChart/values.yaml#L244
    #
    #       Therefore, we need to append NOT replace, but append.
    #       This is done using the `-` at the end of the `path`
    #
    #
    #
    # Additionally, as of 6/26/2025, EFA is NOT a standard add-on for EKS
    # The standard add-ons use logic to detemrine the correct image URI (e.g. https://github.com/aws/amazon-vpc-cni-k8s/blob/fe8968d43ee48a86561faf66f9ea93d794519bd1/charts/aws-vpc-cni/templates/_helpers.tpl#L66)
    # However, as of 6/26/2025, EFA Helm only uses static values.yml.
    # Therefore, the image URI must be overridden manually.
    # The registries are listed here https://docs.aws.amazon.com/eks/latest/userguide/add-ons-images.html
    #
    # NOTE: For now, resolve image URI for only few regions where we support for GA: eu-north-1, us-east-1
    #       These have the same source account ID and are in standard AWS partition
    #
    # NOTE: this should be changed/removed once EFA is added as a standard add-on for EKS
    #####################################################
 
    # TODO: Remove this logic once EFA is an official EKS Add-On and image URI can be deteremined automatically
    # This is ok for GA 6/26/2025 since region support limited to us-east-1, eu-north-1  which have same account ID and partition for source registry
    # https://docs.aws.amazon.com/eks/latest/userguide/add-ons-images.html
    local region=$(kubectl config current-context | cut -d':' -f4)
    local image=$(kubectl get daemonset $EFA -n kube-system -o yaml | yq e '.spec.template.spec.containers[] | select(.name == "aws-efa-k8s-device-plugin").image' -)
    local new_image=$(echo "$image" | sed "s/\.[^.]*\.amazonaws\.com/.$region.amazonaws.com/")
    local index=$(kubectl get daemonset $EFA -n kube-system -o yaml | yq e '.spec.template.spec.containers | to_entries | .[] | select(.value.name == "aws-efa-k8s-device-plugin") | .key' -)

    # Using kubectl directly since relatively simple patch 
    # that does not require new separeate file/deployments specific for RIG
    
    kubectl patch daemonset $EFA -n kube-system --type=json -p='[
      {
        "op": "add",
        "path": "/spec/template/spec/tolerations/-",
        "value": {
          "key": "sagemaker.amazonaws.com/RestrictedNode",
          "value": "Worker",
          "effect": "NoSchedule"
        }
      },
      {
        "op": "replace",
        "path": "/spec/template/spec/containers/'$index'/image",
        "value": "'$new_image'"
      },
      {
        "op": "add",
        "path": "/metadata/annotations/rig.hyperpod.patch~1aws-efa-k8s-device-plugin",
        "value": "{\"timestamp\": \"'$DATETIME'\"}"
      }
    ]'
}

in_list() {
    local item="$1"
    shift
    local -a skiplist=("$@")
    for x in "${skiplist[@]}"; do
        if [[ "$item" == "$x" ]]; then
            return 0  # True, item is in skiplist
        fi
    done
    return 1  # False, item is not in skiplist
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
	if ! in_list "$name" "${PATCH_ONLY[@]}" ; then
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
	    if in_list "$name" "${PATCH_ONLY[@]}"; then
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
    helm template $RIG_HELM_RELEASE ./HyperPodHelmChartForRIG --namespace kube-system -f ./HyperPodHelmChartForRIG/values.yaml > $outpath
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
      helm upgrade --install $RIG_HELM_RELEASE ./HyperPodHelmChartForRIG --namespace kube-system -f ./HyperPodHelmChartForRIG/values.yaml
      if [ $? -ne 0 ]; then
        echo "RIG Helm Installation Failed. Exiting (0/4 steps completed)..."
        return 1
      fi
  
      # aws-node needs specific instllation for *.nonrig.yaml
      local patched=$(kubectl get daemonset aws-node -n kube-system -o yaml | yq e '.metadata.annotations | has("rig.hyperpod.patch/aws-node")' -)
      if [ "$patched" = "false" ]; then
          kubectl apply -f HyperPodHelmChartForRIG/charts/aws-node/templates/daemonset.nonrig.yaml -n kube-system
          if [ $? -ne 0 ]; then
            echo "RIG Helm Installation Failed (aws-node). Exiting (only 1/4 steps completed)..."
            return 1
          fi
      else
          echo "Found annotation 'rig.hyperpod.patch/aws-node'. Skipping patching for RIG..."
      fi

      # training-operator needs specific patch
      patched=$(kubectl get deployments $TRAINING_OPERATORS -n kubeflow -o yaml | yq e '.metadata.annotations | has("rig.hyperpod.patch/training-operators")' -)
      if [ "$patched" = "false" ]; then
          override_training_operators
          if [ $? -ne 0 ]; then
            echo "RIG Helm Installation Failed (training-operator). Exiting (only 2/4 steps completed)..."
            return 1
          fi
      else
          echo "Found annotation 'rig.hyperpod.patch/training-operators'. Skipping patching for RIG..."
      fi

      # efa needs specific patch
      patched=$(kubectl get daemonset $EFA -n kube-system -o yaml | yq e '.metadata.annotations | has("rig.hyperpod.patch/aws-efa-k8s-device-plugin")' -)
      if [ "$patched" = "false" ]; then
          override_efa
          if [ $? -ne 0 ]; then
            echo "RIG Helm Installation Failed (aws-efa-k8s-device-plugin). Exiting (only 3/4 steps completed)..."
            return 1
          fi
      else
          echo "Found annotation 'rig.hyperpod.patch/aws-efa-k8s-device-plugin'. Skipping patching for RIG..."
      fi

      echo ""
      echo "✅ RIG Helm Installation Succeeded (4/4 steps completed)."
      echo ""

      # Warn user about CNI start up
      echo ""
      echo "⚠️ Note: aws-node (AWS VPC CNI) is a critical add-on for general pod use."
      echo "Other pods that depend on aws-node (e.g. CoreDNS, HyperPod HealthMonitoringAgent,...) may experience 'FailedCreatePodSandBox' if the aws-node pods are not available before start up."
      echo "Therefore, please allow additional time for K8s to recreate the pods and/or manually recreate the pods (or let K8s recreate after cleaning up) before full cluster use."
      echo ""
     
      # Warn user about HMA region
      echo ""
      echo "⚠️ Note: HyperPod HealthMonitoringAgent (HMA) is a critical dependency for node resilience."
      echo "HMA installation is normally handled by the standard (non-RIG) Helm Chart. See https://github.com/aws/sagemaker-hyperpod-cli/blob/main/helm_chart/HyperPodHelmChart/charts/health-monitoring-agent/values.yaml#L2"
      echo "The image URI for this component is region-specific. See https://github.com/aws/sagemaker-hyperpod-cli/tree/main/helm_chart#6-notes"
      echo "To ensure this feature works as intended, please be sure to use the correct image URI."
      echo ""
      echo "For installations that have already deployed, the image URI can be updated (corrected) using a 'kubectl patch' command. For example:"
      echo "    kubectl patch daemonset health-monitoring-agent -n aws-hyperpod --patch '{"spec": {"template": {"spec": {"containers": [{"name": "health-monitoring-agent", "image": "767398015722.dkr.ecr.us-east-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.448.0_1.0.115.0"}]}}}}'"
      echo ""

      # Warn user about re-running installation
      echo ""
      echo "⚠️ Note: This installation script should only be run one time for a given HyperPod cluster. Please avoid re-running this installation to avoid duplicated Deployments and Daemonsets and unintended K8s patches to existing objects."
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

assert_supported_region() {
    local eks=$(kubectl config current-context)
    local region=$(kubectl config current-context | cut -d':' -f4)
    if ! in_list "$region" "${SUPPORTED_REGIONS[@]}" ; then
        echo ""
	echo "❌  Installation cancelled (no actions taken)."
	echo "'kubectl config current-context' discovered cluster is in region '$region.' (eks cluster '$eks')"
        echo "The list of SUPPORTED_REGIONS for HyperPod RIG use/RIG Helm installation is [${SUPPORTED_REGIONS[@]}]."
        echo "Please use one of these supported regions for HyperPod RIG use."
        echo ""
        exit 1
    fi
}

assert_not_already_installed() {
    if helm status $RIG_HELM_RELEASE -n kube-system >/dev/null 2>&1; then
        echo ""
        echo "⚠️  WARNING: It looks like this cluster already has RIG dependencies installed (found '$RIG_HELM_RELEASE' Helm release in EKS cluster)" 
        echo "This installation script should only be run one time for a given HyperPod cluster. Please avoid re-running this installation to avoid duplicated Deployments and Daemonsets and unintended K8s patches to existing objects."
        echo ""
        
        read -p "Are you sure you want to re-run this RIG Helm installation script ? [y/N]: " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            echo ""
            echo "⚠️  WARNING: Re-running installation for cluster with RIG dependencies already installed..."
            echo ""
        else
            echo ""
            echo "❌  Installation cancelled."
            echo ""
            exit 1
        fi 
    fi
}

get_standard_hyperpod_helm_release_name() {
    release_name=$(kubectl get namespace aws-hyperpod -o yaml | yq '.metadata.annotations."meta.helm.sh/release-name"')
    if [ -z "$release_name" ] || [ "$release_name" = "null" ] ; then
        echo "Error: Namespace 'aws-hyperpod' does not exist. Please be sure to install the HyperPod standard Helm chart (https://github.com/aws/sagemaker-hyperpod-cli/tree/main/helm_chart#step-three)" >&2
        return 1
    else
        echo "Found Namespace 'aws-hyperpod' installed with Helm release name: $release_name" >&2
        echo "$release_name"
        return 0
    fi
}

main() {
    assert_not_already_installed

    ensure_yq_installed
    
    set_script_variables

    assert_supported_region
    assert_addons_enabled add_ons[@]

    set -e
    fetch_yaml_and_enable_overrides add_ons[@]

    local outpath="./rig-dependencies.yaml"
    refresh_helm_dependencies
    render_rig_helm_chart $outpath
    confirm_installation_with_user $outpath
}

main
