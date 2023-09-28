from aws_ecr import ECR
from aws_ecs import ECS

class ECSCluster:
    @staticmethod
    def create_cluster(prefix, project_name, environment):
        tags = {
            "Environment": environment,
            "Service": project_name
        }

        resource_name = f"{prefix}{project_name}"

        ecr_repo = ECR.create_repository(
            name=f"{resource_name}",
            image_tag_mutability="MUTABLE",
            image_scanning_configuration={
                "scanOnPush": True
            },
            tags=tags
        )

        ecs_cluster = ECS.create_cluster(
            name=f"{resource_name}",
            container_insights_enabled=True,
            tags=tags
        )

        cluster = {
            "ecr_repo_name": f"{resource_name}",
            "ecr_repo_arn": ecr_repo.arn,
            "ecs_cluster_arn": ecs_cluster.arn
        }

        return cluster
