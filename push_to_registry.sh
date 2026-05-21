#!/bin/bash
set -euo pipefail

IMAGE_NAME="teabeeoh/market_server"
VERSION=$(grep '^version' pyproject.toml | cut -d'"' -f2)
REGISTRY="harbor.stocksbot.de"
#REGISTRY="harbor.fritz.box"

# Image bauen (mit Version- und latest-Tag)
docker buildx build --platform linux/amd64,linux/arm64/v8 \
    -t ${IMAGE_NAME}:${VERSION} \
    -t ${IMAGE_NAME}:latest \
    .

# Images fuer Registry taggen
docker tag ${IMAGE_NAME}:${VERSION} ${REGISTRY}/${IMAGE_NAME}:${VERSION}
docker tag ${IMAGE_NAME}:latest ${REGISTRY}/${IMAGE_NAME}:latest

# Login beim Registry
#docker login ${REGISTRY}

# Images pushen
docker push ${REGISTRY}/${IMAGE_NAME}:${VERSION}
docker push ${REGISTRY}/${IMAGE_NAME}:latest
