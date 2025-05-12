#!/bin/bash

SRC_DIR="HyperPodHelmChart"
OUTPUT_DIR="HyperPodHelmChartForRIG"

# Format: "<eks|hyperpod>,namespace,<k8s_name|chart_dir>"
add_ons=(
    "eks,kube-system,coredns"
    "hp,kube-system,mpi-operator"
    "hp,kube-system,neuron-device-plugin"
    "hp,kube-system,training-operators"
)

fetch_yaml_and_enable_overrides() {
    local resources=("${!1}")
    
    rm -rf $OUTPUT_DIR/charts
    
    for resource in "${resources[@]}"; do
        IFS=',' read -r scope namespace name <<< "$resource"
	echo "Processing $scope add-on called $name in namespace $namespace..."
        
	value_safe_name=${name//-/_} # Convert hyphens to underscores
	cp -r $SRC_DIR/charts/$name $OUTPUT_DIR/charts/$name
	rm -rf $OUTPUT_DIR/charts/$name/templates
	rm -f $OUTPUT_DIR/charts/$name/*.tgz
	mkdir -p $OUTPUT_DIR/charts/$name/templates
	
	if [ "$scope" = "eks" ]; then
		kubectl get deployment $name -n $namespace -o yaml | \
			yq 'select(.kind == "Deployment" or .kind == "DaemonSet")' - | yq e "
		    .metadata.name = \"rig-\" + .metadata.name |
		    .spec.template.spec.nodeSelector = \"NODESELECTORS\" |
		    .spec.template.spec.tolerations = \"TOLERATIONS\"
		" - | \
			sed "s/NODESELECTORS/\n{{ toYaml (index .Values \"nodeSelector\") | indent 8 }}/" | 
			sed "s/TOLERATIONS/\n{{ toYaml (index .Values \"tolerations\"  ) | indent 8 }}/" \
		    > $OUTPUT_DIR/charts/$name/templates/$name.yml


		cat << EOF > $OUTPUT_DIR/charts/$name/Chart.yaml
apiVersion: v2
name: $name
version: 0.1.0
appVersion: 1.0
description: A Helm chart for setting up $name in RIG Workers
EOF


	else
		helm template dependencies $SRC_DIR/charts/$name -f $SRC_DIR/values.yaml -f $SRC_DIR/charts/$name/values.yaml --debug | \
			yq 'select(.kind == "Deployment" or .kind == "DaemonSet")' - | yq e "
		    .metadata.name = \"rig-\" + .metadata.name |
		    .spec.template.spec.nodeSelector = \"NODESELECTORS\" |
		    .spec.template.spec.tolerations = \"TOLERATIONS\"
		" - | \
			sed "s/NODESELECTORS/\n{{ toYaml (index .Values \"nodeSelector\") | indent 8 }}/" | 
			sed "s/TOLERATIONS/\n{{ toYaml (index .Values \"tolerations\"  ) | indent 8 }}/" \
		    > $OUTPUT_DIR/charts/$name/templates/$name.yml
	fi
    done
}

if ! command -v yq &> /dev/null; then
    echo "Error: yq is required but not installed."
    exit 1
fi
fetch_yaml_and_enable_overrides add_ons[@]
helm dependencies update ./HyperPodHelmChartForRIG # This needs to be run after any dependency template change before "helm <template | install>"
helm template rig-dependencies ./HyperPodHelmChartForRIG --namespace kube-system -f ./HyperPodHelmChartForRIG/values.yaml > rig-dependencies.yaml
cat rig-dependencies.yaml
echo
read -p "🚀 Do you want to install this Helm chart? [y/N]: " confirm

if [[ "$confirm" =~ ^[Yy]$ ]]; then
  echo "🔧 Installing Helm chart..."
  helm install rig-dependencies ./HyperPodHelmChartForRIG --namespace kube-system -f ./HyperPodHelmChartForRIG/values.yaml
else
  echo "❌ Installation cancelled."
fi

echo "Templates generated in $OUTPUT_DIR"
echo ""
echo ""
