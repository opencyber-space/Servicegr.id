#!/bin/bash

# Define folder names and image names
declare -A folders_and_images=(
  ["executor"]=""
  ["executor_job"]="policies-executor_job:v1"
  ["executor_server"]="policies-server:v1"
  ["system"]="policies-system:v1"
)

# Loop through each folder and build the Docker image
for folder in "${!folders_and_images[@]}"; do
  echo "Building Docker image for $folder..."
  
  # Change to the folder
  cd "$folder" || { echo "Failed to navigate to $folder"; exit 1; }
  
  # Build the Docker image
  docker build -t "${folders_and_images[$folder]}" .
  
  # Check if the build succeeded
  if [ $? -eq 0 ]; then
    echo "Docker image ${folders_and_images[$folder]} built successfully."
  else
    echo "Failed to build Docker image ${folders_and_images[$folder]}."
    exit 1
  fi
  
  # Return to the root directory
  cd ..
done

echo "All Docker images built successfully!"
