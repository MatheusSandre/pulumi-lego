import pulumi
import pulumi_aws as aws

from aws_iam import IAM
from aws_ecs import ECS
from aws_cloudwatch import Cloudwatch
from aws_ec2 import EC2
from aws_efs import EFS
from aws_servicediscovery import ServiceDiscovery

aws_region = pulumi.Config('aws').get('region')


class Service:
    @staticmethod
    def create_service(cluster, prefix, project_name, service_name, cpu, memory, environment,
                       vpc, policies_roles, alb, app_port, container_definitions_json, volume,
                       service_discovery, ignore_container_definitions_changes,
                       circuit_breaker_enabled):

        tags = {
            "Environment": environment,
            "Service": project_name
        }

        resource_name = f"{prefix}{service_name}"


        if volume == True:
            volume_efs = EFS.create_filesystem(
                name=f"{resource_name}-efs",
                encrypted=True,
                tags=tags
            )

            EFS.create_mounttarget(
                name=f"{resource_name}-efs-mt",
                file_system_id=volume_efs.id,
                subnet_id=vpc["privateSubnetIDs"][0]
            )

            volumes = [
                {
                    "name": f"{resource_name}-efs",
                    "host": None,
                    "dockerVolumeConfiguration": None,
                    "efsVolumeConfiguration": {
                        "transitEncryptionPort": None,
                        "fileSystemId": volume_efs.id,
                        "authorizationConfig": {
                            "iam": "DISABLED",
                            "accessPointId": None},
                        "transitEncryption": "DISABLED",
                        "rootDirectory": "/"}
                }
            ]
        else:
            volumes = []

        if service_discovery == True:
            namespace = ServiceDiscovery.create_private_namespace(
                name=f"{resource_name}.local",
                vpc_id=vpc["vpcID"],
                tags=tags
            )

            servicediscovery = ServiceDiscovery.create_service(
                name=resource_name,
                namespace_id=namespace.id,
                tags=tags
            )

            service_registries = {
                "containerPort": 0,
                "port": 0,
                "registryArn": servicediscovery.arn
            }
        else:
            service_registries=None


        ecs_task_role = IAM.create_role(
            name=f"{resource_name}-role",
            role_statements=[
                aws.iam.GetPolicyDocumentStatementArgs(
                    effect="Allow",
                    principals=[aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="Service",
                        identifiers=["ecs-tasks.amazonaws.com"],
                    )],
                    actions=["sts:AssumeRole"]
                )
            ]
        )

        Cloudwatch.create_log_group(f"/ecs/{resource_name}-deploy")

        task_definition = ECS.create_task_definition(
            name=f"{resource_name}-deploy",
            network_mode="awsvpc",
            cpu=cpu,
            memory=memory,
            requires_compatibilities=["FARGATE"],
            task_role_arn=ecs_task_role.arn,
            execution_role_arn=policies_roles["ecs_task_execution_role"],
            container_definitions=container_definitions_json,
            ignore_container_definitions_changes=ignore_container_definitions_changes
        )

        ecs_sg = EC2.create_security_group(
            name=f"ecs-{resource_name}-sg",
            vpc_id=vpc["vpcID"],
            tags=tags
        )

        EC2.create_sg_rule(
            name=f"ecs-{resource_name}-sg-ingress",
            security_group_id=ecs_sg,
            from_port=0,
            to_port=0,
            protocol="-1",
            rule_type="ingress",
            source_security_group_id=alb['alb_sg']
        )

        EC2.create_sg_rule(
            name=f"ecs-{resource_name}-sg-self-ingress",
            security_group_id=ecs_sg,
            from_port=0,
            to_port=0,
            protocol="-1",
            rule_type="ingress",
            is_self=True
        )

        EC2.create_sg_rule(
            name=f"ecs-{resource_name}-sg-egress",
            security_group_id=ecs_sg,
            from_port=0,
            to_port=0,
            protocol="-1",
            rule_type="egress",
            cidr_blocks=["0.0.0.0/0"]
        )

        ECS.create_service(
            name=resource_name,
            cluster_arn=cluster['ecs_cluster_arn'],
            task_definition=task_definition.family,
            enable_ecs_managed_tags=True,
            deployment_circuit_breaker={
                "enable": circuit_breaker_enabled,
                "rollback": circuit_breaker_enabled
            },
            propagate_tags="SERVICE",
            enable_execute_command=True,
            load_balancers=[
                {
                    "containerName": project_name,
                    "containerPort": app_port,
                    "targetGroupArn": alb['target_group']
                }
            ],
            network_configuration={
                "assignPublicIp": False,
                "securityGroups": [ecs_sg],
                "subnets": vpc["privateSubnetIDs"]
            },
            capacity_provider_strategies=[
                {
                    "capacityProvider": "FARGATE_SPOT",
                    "base": 0,
                    "weight": 3
                }
            ],
            service_registries=service_registries,
            deployment_minimum_healthy_percent=100,
            deployment_maximum_percent=200,
            tags=tags
        )

        # if environment == "production":
        #     ECS.create_service(
        #         name=f"{resource_name}-on-demand",
        #         cluster_arn=cluster['ecs_cluster_arn'],
        #         task_definition=task_definition.family,
        #         enable_ecs_managed_tags=True,
        #         deployment_circuit_breaker={
        #             "enable": circuit_breaker_enabled,
        #             "rollback": circuit_breaker_enabled
        #         },
        #         propagate_tags="SERVICE",
        #         enable_execute_command=True,
        #         load_balancers=[
        #             {
        #                 "containerName": project_name,
        #                 "containerPort": app_port,
        #                 "targetGroupArn": alb['target_group']
        #             }
        #         ],
        #         network_configuration={
        #             "assignPublicIp": False,
        #             "securityGroups": [ecs_sg],
        #             "subnets": vpc["privateSubnetIDs"]
        #         },
        #         capacity_provider_strategies=[
        #             {
        #                 "capacityProvider": "FARGATE",
        #                 "base": 0,
        #                 "weight": 3
        #             }
        #         ],
        #         deployment_minimum_healthy_percent=100,
        #         deployment_maximum_percent=200,
        #         tags=tags
        #     )

        service_values = {
            "sg": ecs_sg,
            "iam_role": ecs_task_role
        }

        return service_values
