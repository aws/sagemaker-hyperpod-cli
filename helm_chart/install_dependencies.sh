#!/bin/bash

# Function to check the status of the last command and exit if it failed
check_status() {
  if [ $? -ne 0 ]; then
    echo "An error occurred during the installation. Exiting."
    exit 1
  fi
}

check_status

set -e  # Exit on any error

# Function to check if command succeeded
check_success() {
    if [ $? -ne 0 ]; then
        echo "Error: $1"
        exit 1
    fi
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install helm if not exists
if command_exists helm; then
    echo "helm is already installed. Version: $(helm version)"
else
    echo "Installing helm..."
    curl -fsSL -o /tmp/get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
    check_success "Failed to download Helm installation script"

    chmod 700 /tmp/get_helm.sh
    /tmp/get_helm.sh
    check_success "Helm installation failed"
fi

# Determine architecture
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    KUBECTL_ARCH="amd64"
else
    KUBECTL_ARCH="arm64"
fi

# Install kubectl if not exists
if command_exists kubectl; then
    echo "kubectl is already installed. Version: $(kubectl version --client)"
else
    echo "Installing kubectl..."
    KUBECTL_VERSION=$(curl -L -s https://dl.k8s.io/release/stable.txt)
    curl -LO -sS "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${KUBECTL_ARCH}/kubectl"
    curl -LO -sS "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${KUBECTL_ARCH}/kubectl.sha256"

    # Verify kubectl checksum
    if echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check; then
        mv kubectl /tmp
        chmod +x /tmp/kubectl
        sudo mv /tmp/kubectl /usr/local/bin
        check_success "Failed to install kubectl"
    else
        echo "kubectl checksum verification failed"
        exit 1
    fi
fi

# Install eksctl if not exists
if command_exists eksctl; then
    echo "eksctl is already installed. Version: $(eksctl version)"
else
    echo "Installing eksctl..."
    SYSTEM=$(uname -s)
    PLATFORM="${SYSTEM}_${KUBECTL_ARCH}"
    EKSCTL_FILE="eksctl_${PLATFORM}.tar.gz"

    curl -sLO "https://github.com/eksctl-io/eksctl/releases/latest/download/${EKSCTL_FILE}"
    check_success "Failed to download eksctl"

    # Verify eksctl checksum
    if curl -sL "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_checksums.txt" | grep $PLATFORM | sha256sum --check; then
        tar -xzf "./${EKSCTL_FILE}" -C /tmp
        rm "./${EKSCTL_FILE}"
        sudo mv /tmp/eksctl /usr/local/bin
        check_success "Failed to install eksctl"
    else
        echo "eksctl checksum verification failed"
        exit 1
    fi
fi

echo "Installation check completed successfully!"
echo "Installed versions:"
echo "helm: $(helm version)"
echo "kubectl: $(kubectl version --client)"
echo "eksctl: $(eksctl version)"

echo "All dependencies installed successfully."
