#!/bin/bash

# Define container names and corresponding images
declare -A containers_and_images=(
  ["executor_api"]="policies-executor_api:v1"
  # ["executor_job"]="policies-executor_job:v1"
  # ["server"]="policies-server:v1"
  ["system"]="policies-system:v1"
)

for container in "${!containers_and_images[@]}"; do
  echo "Starting container $container..."
  
  docker run --name "$container" -v $HOME/Documents/aiosv1/policies:/opt/policies --net=host -d --rm "${containers_and_images[$container]}"
  
  if [ $? -eq 0 ]; then
    echo "Container $container started successfully."
  else
    echo "Failed to start container $container."
  fi
done

echo "All containers started successfully!"
