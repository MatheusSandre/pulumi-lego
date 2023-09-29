import pulumi_aws as aws
from aws_lambda import Lambda
from aws_iam import IAM
from aws_lambda_deployment_pipeline import LambdaDeploymentPipeline
from aws_ec2 import EC2


class LambdaFunction:
    @staticmethod
    def create_function(prefix, function_name, project_name, environment, timeout, memory_size, variables, vpc, version_name, git_branch,
                        git_repo, main_path, aws_region, policies_roles, codestar_arn, sns_notification_arn, s3_codepipeline, tags):

        resource_name = f"{prefix}{project_name}"

        function_role = IAM.create_role(
            name=f"{resource_name}-{function_name}-role",
            role_statements=[
                aws.iam.GetPolicyDocumentStatementArgs(
                    effect="Allow",
                    principals=[aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="Service",
                        identifiers=["lambda.amazonaws.com"],
                    )],
                    actions=["sts:AssumeRole"]
                )
            ]
        )

        IAM.attach_policy_into_role(
            resource_name=f"iamrolepolicyattachment-{resource_name}-{function_name}-role-lambda-basic-execution-policy",
            role=function_role,
            policy=policies_roles["lambda_basic_execution_policy"]
        )

        IAM.attach_policy_into_role(
            resource_name=f"iamrolepolicyattachment-{resource_name}-{function_name}-role-lambda-get-parameter-policy",
            role=function_role,
            policy=policies_roles["get_parameters_policy"]
        )

        if vpc:
            lambda_sg = EC2.create_security_group(
                name=f"lambda-{resource_name}-{function_name}-sg",
                vpc_id=vpc["vpcID"],
                tags=tags
            )
            EC2.create_sg_rule(
                name=f"lambda-{resource_name}-{function_name}-sg-self-ingress",
                security_group_id=lambda_sg,
                from_port=0,
                to_port=0,
                protocol="-1",
                rule_type="ingress",
                is_self=True
            )
            EC2.create_sg_rule(
                name=f"lambda-{resource_name}-{function_name}-sg-egress",
                security_group_id=lambda_sg,
                from_port=0,
                to_port=0,
                protocol="-1",
                rule_type="egress",
                cidr_blocks=["0.0.0.0/0"]
            )
            vpc_config = {
                "security_group_ids": [lambda_sg.id],
                "subnet_ids": vpc["privateSubnetIDs"]
            }
            IAM.attach_policy_into_role(
                resource_name=f"iamrolepolicyattachment-{resource_name}-{function_name}-role-lambda-vpc-execution-policy",
                role=function_role,
                policy=policies_roles["lambda_vpc_execution_policy"]
            )
        else:
            vpc_config = None
            lambda_sg = None

        function = Lambda.create_function(
            name=f"{resource_name}-{function_name}",
            handler="main",
            runtime="go1.x",
            timeout=timeout,
            memory_size=memory_size,
            role=function_role.arn,
            tags=tags,
            environment=variables,
            vpc_config=vpc_config
        )

        alias = Lambda.create_alias(
            name=version_name,
            function_name=f"{resource_name}-{function_name}",
            function_version="$LATEST",
            depends_on=[function]
        )

        LambdaDeploymentPipeline.create_resources(
            branch_name=git_branch,
            git_repo=git_repo,
            lambda_name_in_aws=f"{resource_name}-{function_name}",
            path_begin=".",
            main_path=main_path,
            version=version_name,
            tags=tags,
            aws_region=aws_region,
            policies_roles=policies_roles,
            codestar_arn=codestar_arn,
            sns_notification_arn=sns_notification_arn,
            s3_codepipeline=s3_codepipeline
        )

        function_values={
            "sg": lambda_sg,
            "function_version": alias.arn,
            "function_role": function_role,
            "function": function.arn,
            "name": function_name
        }

        return function_values
