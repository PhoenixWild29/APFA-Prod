from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_ec2 as ec2,
    aws_ecs_patterns as ecs_patterns,
    aws_sagemaker as sagemaker,
    aws_iam as iam,
    core
)
from constructs import Construct

class SilkRiverStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # VPC and Cluster
        vpc = ec2.Vpc(self, "Vpc", max_azs=2)
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        # ECR Repo for Docker Image
        repo = ecr.Repository(self, "Repo")

        # SageMaker Endpoint for LLM
        model_role = iam.Role(self, "SageMakerRole", assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"))
        model_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"))
        sagemaker.CfnModel(self, "LLMModel",
            execution_role_arn=model_role.role_arn,
            primary_container={
                "image": "763104351884.dkr.ecr.us-east-1.amazonaws.com/huggingface-pytorch-inference:2.0.0-transformers4.28.1-gpu-py310-cu118-ubuntu20.04",
                "model_data_url": "s3://your-bucket/llama-model.tar.gz"
            }
        )

        # Fargate Service for App
        ecs_patterns.ApplicationLoadBalancedFargateService(self, "Service",
            cluster=cluster,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(repo),
                container_port=8000
            ),
            public_load_balancer=True
        )

app = core.App()
SilkRiverStack(app, "SilkRiverStack")
app.synth()
