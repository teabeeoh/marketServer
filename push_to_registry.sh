#!/bin/bash

IMAGE_NAME="marketserver"
TAG="latest"
REGISTRY="docker.fritz.box:5000"

# Image bauen
docker build -t ${IMAGE_NAME}:${TAG} .

# Image taggen
docker tag ${IMAGE_NAME}:${TAG} ${REGISTRY}/${IMAGE_NAME}:${TAG}

# Login beim Registry
#docker login ${REGISTRY}

# Image pushen
docker push ${REGISTRY}/${IMAGE_NAME}:${TAG}
