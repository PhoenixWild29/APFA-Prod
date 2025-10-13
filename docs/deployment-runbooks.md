# Deployment Runbooks - Multi-Cloud

**Version:** 1.0  
**Last Updated:** 2025-10-11  
**Owner:** DevOps / SRE Team  
**Status:** Production-Ready

---

## Table of Contents

1. [Overview](#overview)
2. [AWS Deployment](#aws-deployment-ecs-fargate--cdk)
3. [Azure Deployment](#azure-deployment-aks--terraform)
4. [GCP Deployment](#gcp-deployment-gke--helm)
5. [Docker Compose (Local/Staging)](#docker-compose-localstaging)
6. [Zero-Downtime Deployment Strategies](#zero-downtime-deployment-strategies)
7. [Rollback Procedures](#rollback-procedures)
8. [Disaster Recovery](#disaster-recovery)
9. [Security & Compliance](#security--compliance)
10. [Troubleshooting](#troubleshooting)

---

## Overview

### Supported Platforms

| Platform | Orchestration | IaC Tool | Maturity | Recommended For |
|----------|--------------|----------|----------|-----------------|
| **AWS** | ECS Fargate | AWS CDK | ✅ Production | Most teams (AWS-native) |
| **Azure** | AKS (Kubernetes) | Terraform | ✅ Production | Azure-first organizations |
| **GCP** | GKE (Kubernetes) | Helm + Terraform | ✅ Production | Multi-cloud, Kubernetes preference |
| **Docker Compose** | Docker Compose | docker-compose.yml | ⚠️ Dev/Staging | Local development |

### Architecture Comparison

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS (ECS Fargate)                           │
├─────────────────────────────────────────────────────────────────────┤
│  ALB → ECS Service (4-8 tasks) → ElastiCache Redis → S3/MinIO      │
│  • Serverless containers                                            │
│  • Auto-scaling (target: 70% CPU)                                   │
│  • VPC with public/private subnets                                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         Azure (AKS)                                 │
├─────────────────────────────────────────────────────────────────────┤
│  App Gateway → AKS Cluster (3-5 nodes) → Redis Cache → Blob Storage│
│  • Kubernetes-native                                                │
│  • Horizontal Pod Autoscaler (HPA)                                  │
│  • Virtual Network with service endpoints                           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         GCP (GKE)                                   │
├─────────────────────────────────────────────────────────────────────┤
│  Load Balancer → GKE Cluster (3-5 nodes) → Memorystore → GCS       │
│  • Autopilot or Standard GKE                                        │
│  • Workload Identity (secure)                                       │
│  • VPC-native cluster                                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## AWS Deployment (ECS Fargate + CDK)

### Prerequisites

```bash
# Install AWS CLI
brew install awscli  # macOS
# OR
pip install awscli

# Install AWS CDK
npm install -g aws-cdk

# Install Python dependencies
pip install aws-cdk-lib constructs

# Configure AWS credentials
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region: us-east-1
# Default output format: json
```

### Project Structure

```
infra/aws/
├── app.py                 # CDK app entry point
├── cdk_stack.py          # Main stack definition
├── requirements.txt      # Python dependencies
├── cdk.json              # CDK configuration
└── README.md
```

### CDK Stack Implementation

**File:** `infra/aws/cdk_stack.py`

```python
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticache as elasticache,
    aws_s3 as s3,
    aws_ecr as ecr,
    aws_logs as logs,
    aws_iam as iam,
    aws_cloudfront as cloudfront,
    Duration,
    RemovalPolicy,
)
from constructs import Construct

class APFAStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ========================================
        # VPC
        # ========================================
        vpc = ec2.Vpc(
            self, "APFA-VPC",
            max_azs=2,
            nat_gateways=1,  # Cost optimization
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        # ========================================
        # ECS Cluster
        # ========================================
        cluster = ecs.Cluster(
            self, "APFA-Cluster",
            vpc=vpc,
            container_insights=True,  # Enable CloudWatch Container Insights
        )

        # ========================================
        # ECR Repository
        # ========================================
        apfa_repo = ecr.Repository(
            self, "APFA-Repo",
            repository_name="apfa",
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    max_image_count=10,  # Keep last 10 images
                    description="Retain only 10 most recent images",
                ),
            ],
        )

        celery_repo = ecr.Repository(
            self, "Celery-Repo",
            repository_name="apfa-celery",
            removal_policy=RemovalPolicy.RETAIN,
        )

        # ========================================
        # S3 Bucket (MinIO alternative)
        # ========================================
        embeddings_bucket = s3.Bucket(
            self, "Embeddings-Bucket",
            bucket_name=f"apfa-embeddings-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    expiration=Duration.days(90),
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30),
                        ),
                    ],
                ),
            ],
        )

        # ========================================
        # ElastiCache Redis
        # ========================================
        redis_subnet_group = elasticache.CfnSubnetGroup(
            self, "Redis-SubnetGroup",
            description="Subnet group for Redis",
            subnet_ids=[subnet.subnet_id for subnet in vpc.private_subnets],
        )

        redis_security_group = ec2.SecurityGroup(
            self, "Redis-SecurityGroup",
            vpc=vpc,
            description="Security group for Redis",
            allow_all_outbound=True,
        )

        redis_cluster = elasticache.CfnCacheCluster(
            self, "Redis-Cluster",
            cache_node_type="cache.t3.small",
            engine="redis",
            num_cache_nodes=1,
            vpc_security_group_ids=[redis_security_group.security_group_id],
            cache_subnet_group_name=redis_subnet_group.ref,
        )

        # ========================================
        # Task Definition - APFA API
        # ========================================
        apfa_task_definition = ecs.FargateTaskDefinition(
            self, "APFA-TaskDef",
            memory_limit_mib=4096,
            cpu=2048,
        )

        # Grant S3 access
        embeddings_bucket.grant_read_write(apfa_task_definition.task_role)

        apfa_container = apfa_task_definition.add_container(
            "APFA-Container",
            image=ecs.ContainerImage.from_ecr_repository(apfa_repo, "latest"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="apfa",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
            environment={
                "MINIO_ENDPOINT": embeddings_bucket.bucket_name,
                "AWS_REGION": self.region,
                "REDIS_URL": f"redis://{redis_cluster.attr_redis_endpoint_address}:6379",
            },
            secrets={
                "JWT_SECRET": ecs.Secret.from_secrets_manager(
                    self.node.try_get_context("jwt_secret")
                ),
            },
        )

        apfa_container.add_port_mappings(
            ecs.PortMapping(container_port=8000, protocol=ecs.Protocol.TCP)
        )

        # ========================================
        # ALB Fargate Service - APFA API
        # ========================================
        apfa_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "APFA-Service",
            cluster=cluster,
            task_definition=apfa_task_definition,
            desired_count=4,
            public_load_balancer=True,
            health_check_grace_period=Duration.seconds(60),
        )

        # Health check
        apfa_service.target_group.configure_health_check(
            path="/health",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(10),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3,
        )

        # Auto-scaling
        scaling = apfa_service.service.auto_scale_task_count(
            min_capacity=4,
            max_capacity=16,
        )

        scaling.scale_on_cpu_utilization(
            "CPUScaling",
            target_utilization_percent=70,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )

        # ========================================
        # Task Definition - Celery Worker
        # ========================================
        celery_task_definition = ecs.FargateTaskDefinition(
            self, "Celery-TaskDef",
            memory_limit_mib=8192,
            cpu=4096,
        )

        embeddings_bucket.grant_read_write(celery_task_definition.task_role)

        celery_container = celery_task_definition.add_container(
            "Celery-Container",
            image=ecs.ContainerImage.from_ecr_repository(celery_repo, "latest"),
            command=[
                "celery", "-A", "app.tasks", "worker",
                "--loglevel=info",
                "--queues=embedding,indexing,maintenance",
                "--concurrency=4",
            ],
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="celery",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
            environment={
                "CELERY_BROKER_URL": f"redis://{redis_cluster.attr_redis_endpoint_address}:6379/0",
                "CELERY_RESULT_BACKEND": f"redis://{redis_cluster.attr_redis_endpoint_address}:6379/0",
                "MINIO_ENDPOINT": embeddings_bucket.bucket_name,
            },
        )

        # ========================================
        # Celery Worker Service
        # ========================================
        celery_service = ecs.FargateService(
            self, "Celery-Service",
            cluster=cluster,
            task_definition=celery_task_definition,
            desired_count=4,
            enable_execute_command=True,  # For debugging
        )

        # Auto-scaling based on queue depth (custom metric)
        celery_scaling = celery_service.auto_scale_task_count(
            min_capacity=2,
            max_capacity=8,
        )

        # ========================================
        # Outputs
        # ========================================
        from aws_cdk import CfnOutput

        CfnOutput(
            self, "LoadBalancerDNS",
            value=apfa_service.load_balancer.load_balancer_dns_name,
            description="ALB DNS name",
        )

        CfnOutput(
            self, "RedisEndpoint",
            value=redis_cluster.attr_redis_endpoint_address,
            description="Redis endpoint",
        )

        CfnOutput(
            self, "EmbeddingsBucket",
            value=embeddings_bucket.bucket_name,
            description="S3 bucket for embeddings",
        )
```

### Deployment Steps

```bash
# 1. Navigate to infra directory
cd infra/aws

# 2. Install dependencies
pip install -r requirements.txt

# 3. Bootstrap CDK (first time only)
cdk bootstrap aws://ACCOUNT-ID/us-east-1

# 4. Synthesize CloudFormation template
cdk synth

# 5. Deploy stack
cdk deploy --require-approval never

# 6. Wait for deployment (15-20 minutes)
# Stack outputs will show:
# - LoadBalancerDNS
# - RedisEndpoint
# - EmbeddingsBucket
```

### Build & Push Docker Images

```bash
# 1. Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com

# 2. Build APFA image
docker build -t apfa:latest .

# 3. Tag image
docker tag apfa:latest ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/apfa:latest

# 4. Push image
docker push ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/apfa:latest

# 5. Force new deployment
aws ecs update-service --cluster APFA-Cluster --service APFA-Service --force-new-deployment
```

### Post-Deployment Validation

```bash
# 1. Get ALB DNS
ALB_DNS=$(aws cloudformation describe-stacks --stack-name APFAStack --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' --output text)

# 2. Health check
curl http://$ALB_DNS/health
# Expected: {"status":"healthy"}

# 3. Metrics endpoint
curl http://$ALB_DNS/metrics | grep apfa_

# 4. Check ECS tasks
aws ecs list-tasks --cluster APFA-Cluster --service-name APFA-Service
# Expected: 4 running tasks

# 5. Check logs
aws logs tail /ecs/apfa --follow
```

---

## Azure Deployment (AKS + Terraform)

### Prerequisites

```bash
# Install Azure CLI
brew install azure-cli  # macOS
# OR
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Terraform
brew install terraform

# Install kubectl
brew install kubectl

# Login to Azure
az login

# Set subscription
az account set --subscription "YOUR-SUBSCRIPTION-ID"
```

### Project Structure

```
infra/azure/
├── main.tf               # Main Terraform configuration
├── variables.tf          # Input variables
├── outputs.tf            # Output values
├── terraform.tfvars      # Variable values
├── kubernetes/
│   ├── apfa-deployment.yaml
│   ├── celery-deployment.yaml
│   ├── redis-deployment.yaml
│   └── ingress.yaml
└── README.md
```

### Terraform Configuration

**File:** `infra/azure/main.tf`

```hcl
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
  
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "apfaterraformstate"
    container_name       = "tfstate"
    key                  = "apfa.tfstate"
  }
}

provider "azurerm" {
  features {}
}

# ========================================
# Resource Group
# ========================================
resource "azurerm_resource_group" "apfa" {
  name     = "apfa-${var.environment}-rg"
  location = var.location
  
  tags = {
    Environment = var.environment
    Project     = "APFA"
  }
}

# ========================================
# Virtual Network
# ========================================
resource "azurerm_virtual_network" "apfa" {
  name                = "apfa-vnet"
  resource_group_name = azurerm_resource_group.apfa.name
  location            = azurerm_resource_group.apfa.location
  address_space       = ["10.0.0.0/16"]
}

resource "azurerm_subnet" "aks" {
  name                 = "aks-subnet"
  resource_group_name  = azurerm_resource_group.apfa.name
  virtual_network_name = azurerm_virtual_network.apfa.name
  address_prefixes     = ["10.0.1.0/24"]
}

# ========================================
# AKS Cluster
# ========================================
resource "azurerm_kubernetes_cluster" "apfa" {
  name                = "apfa-${var.environment}-aks"
  location            = azurerm_resource_group.apfa.location
  resource_group_name = azurerm_resource_group.apfa.name
  dns_prefix          = "apfa-${var.environment}"
  
  default_node_pool {
    name       = "default"
    node_count = 3
    vm_size    = "Standard_D4s_v3"
    vnet_subnet_id = azurerm_subnet.aks.id
    
    enable_auto_scaling = true
    min_count          = 3
    max_count          = 10
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  network_profile {
    network_plugin    = "azure"
    load_balancer_sku = "standard"
  }
  
  tags = {
    Environment = var.environment
  }
}

# ========================================
# Azure Cache for Redis
# ========================================
resource "azurerm_redis_cache" "apfa" {
  name                = "apfa-${var.environment}-redis"
  location            = azurerm_resource_group.apfa.location
  resource_group_name = azurerm_resource_group.apfa.name
  capacity            = 1
  family              = "C"
  sku_name            = "Standard"
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"
  
  redis_configuration {
    maxmemory_policy = "allkeys-lru"
  }
}

# ========================================
# Storage Account (Blob Storage)
# ========================================
resource "azurerm_storage_account" "apfa" {
  name                     = "apfa${var.environment}storage"
  resource_group_name      = azurerm_resource_group.apfa.name
  location                 = azurerm_resource_group.apfa.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  blob_properties {
    versioning_enabled = true
  }
}

resource "azurerm_storage_container" "embeddings" {
  name                  = "embeddings"
  storage_account_name  = azurerm_storage_account.apfa.name
  container_access_type = "private"
}

# ========================================
# Outputs
# ========================================
output "kube_config" {
  value     = azurerm_kubernetes_cluster.apfa.kube_config_raw
  sensitive = true
}

output "redis_hostname" {
  value = azurerm_redis_cache.apfa.hostname
}

output "storage_account_name" {
  value = azurerm_storage_account.apfa.name
}
```

### Deployment Steps

```bash
# 1. Navigate to Azure infra directory
cd infra/azure

# 2. Initialize Terraform
terraform init

# 3. Plan deployment
terraform plan -out=tfplan

# 4. Apply deployment
terraform apply tfplan

# 5. Get AKS credentials
az aks get-credentials --resource-group apfa-prod-rg --name apfa-prod-aks

# 6. Verify connection
kubectl get nodes
# Expected: 3 nodes in Ready state

# 7. Deploy Kubernetes resources
kubectl apply -f kubernetes/
```

### Kubernetes Manifests

**File:** `infra/azure/kubernetes/apfa-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apfa
  namespace: default
spec:
  replicas: 4
  selector:
    matchLabels:
      app: apfa
  template:
    metadata:
      labels:
        app: apfa
    spec:
      containers:
      - name: apfa
        image: apfaacr.azurecr.io/apfa:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: apfa-secrets
              key: redis-url
        - name: STORAGE_ACCOUNT
          value: "apfaprodstorage"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: apfa-service
spec:
  selector:
    app: apfa
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: apfa-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: apfa
  minReplicas: 4
  maxReplicas: 16
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Post-Deployment Validation

```bash
# 1. Get external IP
kubectl get service apfa-service
# Wait for EXTERNAL-IP (takes 2-3 minutes)

# 2. Health check
EXTERNAL_IP=$(kubectl get service apfa-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$EXTERNAL_IP/health

# 3. Check pods
kubectl get pods -l app=apfa
# Expected: 4 pods in Running state

# 4. View logs
kubectl logs -l app=apfa --tail=100 -f
```

---

## GCP Deployment (GKE + Helm)

### Prerequisites

```bash
# Install gcloud CLI
brew install google-cloud-sdk

# Install kubectl
gcloud components install kubectl

# Install Helm
brew install helm

# Login to GCP
gcloud auth login

# Set project
gcloud config set project YOUR-PROJECT-ID
```

### Project Structure

```
infra/gcp/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── helm/
│   └── apfa/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── deployment.yaml
│           ├── service.yaml
│           └── hpa.yaml
└── README.md
```

### Terraform Configuration (GKE)

**File:** `infra/gcp/terraform/main.tf`

```hcl
terraform {
  required_version = ">= 1.0"
  
  backend "gcs" {
    bucket = "apfa-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ========================================
# GKE Cluster
# ========================================
resource "google_container_cluster" "apfa" {
  name     = "apfa-${var.environment}-gke"
  location = var.region
  
  # Autopilot mode (recommended) or Standard
  enable_autopilot = true
  
  # Or for Standard mode:
  # remove_default_node_pool = true
  # initial_node_count       = 1
  
  network    = google_compute_network.apfa.name
  subnetwork = google_compute_subnetwork.apfa.name
  
  ip_allocation_policy {
    cluster_ipv4_cidr_block  = "/16"
    services_ipv4_cidr_block = "/22"
  }
  
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
}

# ========================================
# VPC Network
# ========================================
resource "google_compute_network" "apfa" {
  name                    = "apfa-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "apfa" {
  name          = "apfa-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.apfa.id
}

# ========================================
# Cloud Memorystore (Redis)
# ========================================
resource "google_redis_instance" "apfa" {
  name           = "apfa-redis"
  tier           = "STANDARD_HA"
  memory_size_gb = 5
  region         = var.region
  
  authorized_network = google_compute_network.apfa.id
  
  redis_configs = {
    maxmemory-policy = "allkeys-lru"
  }
}

# ========================================
# Cloud Storage Bucket
# ========================================
resource "google_storage_bucket" "embeddings" {
  name          = "${var.project_id}-embeddings"
  location      = var.region
  force_destroy = false
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# ========================================
# Outputs
# ========================================
output "cluster_name" {
  value = google_container_cluster.apfa.name
}

output "redis_host" {
  value = google_redis_instance.apfa.host
}

output "bucket_name" {
  value = google_storage_bucket.embeddings.name
}
```

### Helm Chart

**File:** `infra/gcp/helm/apfa/values.yaml`

```yaml
replicaCount: 4

image:
  repository: gcr.io/YOUR-PROJECT-ID/apfa
  pullPolicy: IfNotPresent
  tag: "latest"

service:
  type: LoadBalancer
  port: 80
  targetPort: 8000

resources:
  requests:
    memory: "2Gi"
    cpu: "1"
  limits:
    memory: "4Gi"
    cpu: "2"

autoscaling:
  enabled: true
  minReplicas: 4
  maxReplicas: 16
  targetCPUUtilizationPercentage: 70

env:
  - name: REDIS_HOST
    value: "10.0.0.3"  # From Terraform output
  - name: GCS_BUCKET
    value: "YOUR-PROJECT-ID-embeddings"
  - name: JWT_SECRET
    valueFrom:
      secretKeyRef:
        name: apfa-secrets
        key: jwt-secret

celery:
  enabled: true
  replicaCount: 4
  image:
    repository: gcr.io/YOUR-PROJECT-ID/apfa-celery
    tag: "latest"
  resources:
    requests:
      memory: "4Gi"
      cpu: "2"
    limits:
      memory: "8Gi"
      cpu: "4"
```

### Deployment Steps

```bash
# 1. Deploy infrastructure with Terraform
cd infra/gcp/terraform
terraform init
terraform apply

# 2. Get GKE credentials
gcloud container clusters get-credentials apfa-prod-gke --region us-central1

# 3. Build and push Docker image
gcloud builds submit --tag gcr.io/YOUR-PROJECT-ID/apfa:latest .

# 4. Create Kubernetes secrets
kubectl create secret generic apfa-secrets \
  --from-literal=jwt-secret=YOUR-JWT-SECRET \
  --from-literal=api-key=YOUR-API-KEY

# 5. Install Helm chart
cd infra/gcp/helm
helm install apfa ./apfa

# 6. Wait for deployment
kubectl rollout status deployment/apfa

# 7. Get load balancer IP
kubectl get service apfa -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

### Post-Deployment Validation

```bash
# 1. Health check
LB_IP=$(kubectl get service apfa -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$LB_IP/health

# 2. Check pods
kubectl get pods -l app.kubernetes.io/name=apfa

# 3. View logs
kubectl logs -l app.kubernetes.io/name=apfa --tail=100 -f

# 4. Check HPA
kubectl get hpa
```

---

## Docker Compose (Local/Staging)

### Configuration

**File:** `docker-compose.yml` (Already exists, enhanced version)

```yaml
version: '3.8'

services:
  apfa:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MINIO_ENDPOINT=${MINIO_ENDPOINT}
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
      - AWS_REGION=${AWS_REGION}
      - API_KEY=${API_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=false
    volumes:
      - ./app:/app
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  celery_worker:
    build: .
    command: celery -A app.tasks worker --loglevel=info --queues=embedding,indexing,maintenance --concurrency=4
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - MINIO_ENDPOINT=${MINIO_ENDPOINT}
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app
    restart: unless-stopped
    deploy:
      replicas: 2

  celery_beat:
    build: .
    command: celery -A app.tasks beat --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
    volumes:
      - ./app:/app
    restart: unless-stopped

  flower:
    build: .
    command: celery -A app.tasks flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
      - celery_worker
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/alerts.yml:/etc/prometheus/alerts.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=redis-datasource
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana-dashboards:/etc/grafana/provisioning/dashboards
    restart: unless-stopped

volumes:
  redis_data:
  grafana_data:
```

### Deployment

```bash
# 1. Start all services
docker-compose up -d

# 2. Check status
docker-compose ps

# 3. View logs
docker-compose logs -f apfa

# 4. Scale workers
docker-compose up -d --scale celery_worker=4

# 5. Access services
# - API: http://localhost:8000
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000
# - Flower: http://localhost:5555
```

---

## Zero-Downtime Deployment Strategies

### Blue-Green Deployment

**Use Case:** Major version upgrades, database migrations

```bash
# AWS ECS Example

# 1. Deploy green version (new tasks)
aws ecs create-service \
  --cluster APFA-Cluster \
  --service-name APFA-Service-Green \
  --task-definition apfa:2 \
  --desired-count 4 \
  --load-balancers targetGroupArn=arn:aws:...,containerName=apfa,containerPort=8000

# 2. Route 10% traffic to green
aws elbv2 modify-listener \
  --listener-arn arn:aws:... \
  --default-actions Type=forward,ForwardConfig='{
    "TargetGroups":[
      {"TargetGroupArn":"arn:aws:...:target-group/blue","Weight":90},
      {"TargetGroupArn":"arn:aws:...:target-group/green","Weight":10}
    ]
  }'

# 3. Monitor for 15 minutes
watch -n 10 'aws cloudwatch get-metric-statistics ...'

# 4. Gradually shift traffic (50/50, then 100/0)
# ...

# 5. Decommission blue
aws ecs delete-service --cluster APFA-Cluster --service APFA-Service-Blue
```

### Rolling Update (Kubernetes)

```bash
# 1. Update image
kubectl set image deployment/apfa apfa=apfa:v2

# 2. Watch rollout
kubectl rollout status deployment/apfa

# 3. Pause rollout (if issues)
kubectl rollout pause deployment/apfa

# 4. Resume rollout
kubectl rollout resume deployment/apfa

# 5. Rollback if needed
kubectl rollout undo deployment/apfa
```

### Canary Deployment

```yaml
# Kubernetes with Istio
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: apfa
spec:
  hosts:
  - apfa
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: apfa
        subset: v2
  - route:
    - destination:
        host: apfa
        subset: v1
      weight: 90
    - destination:
        host: apfa
        subset: v2
      weight: 10
```

---

## Rollback Procedures

### AWS ECS Rollback

```bash
# 1. Identify previous task definition
aws ecs describe-services \
  --cluster APFA-Cluster \
  --services APFA-Service \
  --query 'services[0].deployments'

# 2. Update service to previous version
aws ecs update-service \
  --cluster APFA-Cluster \
  --service APFA-Service \
  --task-definition apfa:1

# 3. Wait for deployment
aws ecs wait services-stable \
  --cluster APFA-Cluster \
  --services APFA-Service

# Time to rollback: ~5 minutes
```

### Kubernetes Rollback

```bash
# 1. View rollout history
kubectl rollout history deployment/apfa

# 2. Rollback to previous version
kubectl rollout undo deployment/apfa

# 3. Rollback to specific revision
kubectl rollout undo deployment/apfa --to-revision=3

# 4. Verify rollback
kubectl rollout status deployment/apfa

# Time to rollback: ~2 minutes
```

---

## Disaster Recovery

### Backup Strategy

**What to Backup:**
1. **Database:** PostgreSQL (user data)
2. **Embeddings:** S3/Blob Storage/GCS
3. **FAISS Indexes:** MinIO/S3
4. **Configuration:** Secrets, environment variables

**Backup Schedule:**
- **Daily:** Full backup of embeddings and indexes
- **Hourly:** Incremental backup of database
- **Real-time:** Delta Lake transaction logs

### AWS Backup Example

```bash
# 1. Enable versioning (already configured in CDK)
aws s3api put-bucket-versioning \
  --bucket apfa-embeddings \
  --versioning-configuration Status=Enabled

# 2. Create backup vault
aws backup create-backup-vault --backup-vault-name apfa-backup

# 3. Create backup plan (via AWS Console or CLI)

# 4. Test restore
aws s3 sync s3://apfa-embeddings s3://apfa-embeddings-restore
```

### Recovery Time Objective (RTO) / Recovery Point Objective (RPO)

| Component | RTO | RPO | Recovery Procedure |
|-----------|-----|-----|-------------------|
| **API Service** | <5 min | 0 (stateless) | Redeploy from latest image |
| **Redis** | <10 min | <1 hour | Restore from RDB snapshot |
| **Embeddings** | <30 min | <24 hours | Restore from S3 backup |
| **FAISS Index** | <10 min | <1 hour | Rebuild from embeddings or restore |
| **Database** | <15 min | <1 hour | Restore from automated backup |

---

## Security & Compliance

### Secrets Management

**AWS Secrets Manager:**
```bash
# Create secret
aws secretsmanager create-secret \
  --name apfa/prod/jwt-secret \
  --secret-string "your-secret-value"

# Reference in ECS task definition
{
  "secrets": [
    {
      "name": "JWT_SECRET",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:apfa/prod/jwt-secret"
    }
  ]
}
```

**Azure Key Vault:**
```bash
# Create secret
az keyvault secret set \
  --vault-name apfa-keyvault \
  --name jwt-secret \
  --value "your-secret-value"

# Reference in AKS pod
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: apfa
    env:
    - name: JWT_SECRET
      valueFrom:
        secretKeyRef:
          name: apfa-secrets
          key: jwt-secret
```

### Network Security

**Firewall Rules:**
- Allow inbound: 443 (HTTPS), 8000 (API - ALB only)
- Deny all other inbound traffic
- Allow outbound: 443 (AWS APIs), 6379 (Redis - private)

**Security Groups (AWS):**
```hcl
resource "aws_security_group" "apfa" {
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]  # VPC only
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Health Check Failing

**Symptoms:**
- ECS tasks stopping and restarting
- ALB marking targets unhealthy

**Diagnosis:**
```bash
# Check task logs
aws logs tail /ecs/apfa --follow

# Check health endpoint
curl http://<task-ip>:8000/health
```

**Solution:**
```bash
# Increase health check grace period
aws ecs update-service \
  --cluster APFA-Cluster \
  --service APFA-Service \
  --health-check-grace-period-seconds 120
```

#### Issue 2: Redis Connection Timeout

**Symptoms:**
- Celery workers unable to connect
- Cache misses at 100%

**Diagnosis:**
```bash
# Check Redis connectivity
redis-cli -h <redis-endpoint> ping

# Check security group rules
aws ec2 describe-security-groups --group-ids sg-xxx
```

**Solution:**
```bash
# Add ECS task security group to Redis security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-redis \
  --protocol tcp \
  --port 6379 \
  --source-group sg-ecs-tasks
```

---

## Pre-Deployment Checklist

- [ ] All environment variables configured in `.env` or secrets manager
- [ ] Docker images built and pushed to registry
- [ ] Database migrations applied (if applicable)
- [ ] MinIO/S3 bucket created with correct permissions
- [ ] Redis/ElastiCache accessible from application subnet
- [ ] Load balancer health check configured (path: `/health`)
- [ ] Auto-scaling policies configured (target: 70% CPU)
- [ ] Monitoring dashboards imported in Grafana
- [ ] Alerts configured in Prometheus
- [ ] On-call rotation updated in PagerDuty
- [ ] Rollback procedure tested in staging
- [ ] Team notified of deployment window
- [ ] Documentation updated with new endpoints/IPs

---

## Post-Deployment Checklist

- [ ] Health check passing (curl http://<lb-url>/health)
- [ ] Metrics endpoint responding (curl http://<lb-url>/metrics)
- [ ] Authentication working (POST /token)
- [ ] Advice generation working (POST /generate-advice)
- [ ] Celery workers processing tasks (check Flower)
- [ ] Redis connection established (check logs)
- [ ] S3/Blob storage accessible (check MinIO operations)
- [ ] Prometheus scraping metrics (check targets)
- [ ] Grafana dashboards loading (check 3 dashboards)
- [ ] Alerts firing correctly (test with mock alert)
- [ ] Load balancer distributing traffic evenly
- [ ] Auto-scaling triggered at 70% CPU (simulate load)
- [ ] No errors in logs for 30 minutes
- [ ] Performance metrics within SLA (P95 <3s)
- [ ] Cache hit rate >60% (target: 80%)

---

**Document Status:** Production-Ready  
**Last Reviewed:** 2025-10-11  
**Next Review:** Quarterly or after major deployment

---

**For Questions:**
- Slack: #apfa-devops
- Email: apfa-sre@company.com
- PagerDuty: APFA On-Call Rotation

