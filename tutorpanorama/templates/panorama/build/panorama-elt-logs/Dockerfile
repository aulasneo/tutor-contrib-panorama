# AWS public registry: https://gallery.ecr.aws/aws-observability/aws-for-fluent-bit
FROM {{ PANORAMA_FLB_BASE_IMAGE }}

# LABEL about the custom image
LABEL maintainer="devops@aulasneo.com"
LABEL version="0.1"
LABEL description="Panorama logs extraction and load tool for Kubernetes"

# The S3 output uses its native AWS client; no CLI or OS-wide update is needed.
