#!/bin/bash
set -e

SRC_DIR="HyperPodHelmChart"
OUTPUT_DIR="HyperPodHelmChartForRIG"

# Format: "<eks|hyperpod>,namespace,<k8s_name|chart_dir>"
add_ons=(
    "eks,kube-system,aws-node,daemonset"
    "eks,kube-system,coredns,deployment"
    "hp,kube-system,mpi-operator,deployment"
    "hp,kube-system,neuron-device-plugin,daemonset"
    "hp,kube-system,training-operators,deployment"
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
    override_images=$(echo "$set_and_append_envvars" | \
	    yq e -P " 
		.spec.template.spec.containers[] |=
		    select(.name == \"aws-node\").image = \"602401143452.dkr.ecr.us-east-1.amazonaws.com/amazon-k8s-cni:v1.19.6-rc1-eksbuild.1\" |
		.spec.template.spec.containers[] |=
		    select(.name == \"aws-vpc-cni-init\").image = \"602401143452.dkr.ecr.us-east-1.amazonaws.com/amazon/aws-network-policy-agent:v1.2.1-eksbuild.2\"
            " - )
    change_metadata=$(echo "$override_images" | \
	    yq e -P "
                .metadata.name = \"rig-\" + .metadata.name |
		del(.status)
            " - )

    echo "$change_metadata" | yq eval -P '.' - > $outdir/daemonset.rig.yaml

    rm $tmp
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
	rm -rf $OUTPUT_DIR/charts/$name/templates
	rm -f $OUTPUT_DIR/charts/$name/*.tgz
	mkdir -p $OUTPUT_DIR/charts/$name/templates


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
	    else
		get_helm_chart_from_eks $kind $name $namespace | \
		    enable_nodeselectors_and_tolerations_overrides $outpath
            fi
	else
	    cp -r $SRC_DIR/charts/$name/. $OUTPUT_DIR/charts/$name
	    rm -rf $OUTPUT_DIR/charts/$name/templates/*

            get_helm_chart_from_local $SRC_DIR $name $kind | \
               enable_nodeselectors_and_tolerations_overrides $outpath
	fi
    done
}

assert_eks_addons_enabled() {
    local resources=("${!1}")
    local response=""
    for resource in "${resources[@]}"; do
        IFS=',' read -r scope namespace name kind <<< "$resource"
        if [ "$scope" = "eks" ]; then
            if [ "$kind" = "daemonset" ]; then
                response=$(kubectl get daemonset $name -n $namespace --no-headers 2>/dev/null)
            else
                response=$(kubectl get deployment $name -n $namespace --no-headers 2>/dev/null)
            fi
            if [ -z "$response" ]; then
                echo "No $kind $name found in namespace $namespace. Please enable this before installing RIG dependencies."
                exit 1
            fi
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
      helm install rig-dependencies ./HyperPodHelmChartForRIG --namespace kube-system -f ./HyperPodHelmChartForRIG/values.yaml
      
      # aws-node needs specific instllation for *.nonrig.yaml
      kubectl apply -f HyperPodHelmChartForRIG/charts/aws-node/templates/daemonset.nonrig.yaml -n kube-system

    else
      echo "❌ Installation cancelled."
    fi
}

ensure_yq_installed(){
    if ! command -v yq &> /dev/null; then
        echo "Error: yq is required but not installed."
        exit 1
    fi

    version=$(yq --version | grep -o 'v[0-9]\+' | cut -d 'v' -f 2 )
    if [ "$version" -lt "4" ]; then
        echo "Error: yq version 4 or higher is required"
        echo "Current version: $(yq -q --version)"
        echo "Please upgrade yq"
        exit 1
    fi
}

main() {
    ensure_yq_installed

    assert_eks_addons_enabled add_ons[@]
    fetch_yaml_and_enable_overrides add_ons[@]

    local outpath="./rig-dependencies.yaml"
    refresh_helm_dependencies
    render_rig_helm_chart $outpath
    confirm_installation_with_user $outpath
}

main
