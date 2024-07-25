# AWS public registry: https://gallery.ecr.aws/aws-observability/aws-for-fluent-bit
FROM public.ecr.aws/aws-observability/aws-for-fluent-bit:2.32.2.20240627

# LABEL about the custom image
LABEL maintainer="devops@aulasneo.com"
LABEL version="0.1"
LABEL description="Panorama logs extraction and load tool for Kubernetes"

# Update Ubuntu Software repository
RUN yum update -y

# Install unzip
RUN yum install -y unzip

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install
RUN rm awscliv2.zip

# Set the AWS default region
RUN aws configure set region {{ PANORAMA_REGION }}
