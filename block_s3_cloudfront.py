from aws_s3 import S3
from aws_cloudfront import Cloudfront

class S3Cloudfront:
    @staticmethod
    def create_resources(project_name, s3_cors_rules, environment, prefix):
        tags = {
            "Environment": environment,
            "Service": project_name
        }

        resource_name = f"{prefix}{project_name}"

        origin_access_identity = Cloudfront.create_access_identity(
            name=f"{resource_name}-s3-access",
            comment=f"{resource_name}-s3-access",
        )

        bucket = S3.create_bucket(
            name=f"{resource_name}",
            cors_rules=s3_cors_rules,
            tags=tags,
            block_public_access=False
        )

        s3_cloudfront = {
            "bucket": bucket,
            "origin_access_identity": origin_access_identity
        }

        return s3_cloudfront
