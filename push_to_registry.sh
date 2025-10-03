#!/bin/bash

IMAGE_NAME="teabeeoh/market_server"
TAG="latest"
REGISTRY="harbor.stocksbot.de"
#REGISTRY="harbor.fritz.box"

# Image bauen
docker buildx build --platform linux/amd64,linux/arm64/v8 -t ${IMAGE_NAME}:${TAG} .

# Image taggen
docker tag ${IMAGE_NAME}:${TAG} ${REGISTRY}/${IMAGE_NAME}:${TAG}

# Login beim Registry
#docker login ${REGISTRY}

# Image pushen
docker push ${REGISTRY}/${IMAGE_NAME}:${TAG}
