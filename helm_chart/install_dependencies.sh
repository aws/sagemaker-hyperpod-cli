#!/bin/bash

# Function to check the status of the last command and exit if it failed
check_status() {
  if [ $? -ne 0 ]; then
    echo "An error occurred during the installation. Exiting."
    exit 1
  fi
}

check_status

# Add additional dependencies below as needed

# Example: Installing an additional dependency (replace with actual URL)
# echo "Installing Example Dependency..."
# kubectl apply -f "https://example.com/path/to/dependency.yaml"
# check_status

# Add more dependencies here
# echo "Installing Another Dependency..."
# kubectl apply -f "https://example.com/path/to/another-dependency.yaml"
# check_status

echo "All dependencies installed successfully."
