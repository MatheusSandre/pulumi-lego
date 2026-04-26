from aws_s3 import S3
from aws_cloudfront import Cloudfront

class S3Cloudfront:
    @staticmethod
    def create_resources(project_name, s3_cors_rules, environment, prefix, tags):

        resource_name = f"{prefix}{project_name}"

        origin_access_control = Cloudfront.create_origin_access_control(
            name=f"{resource_name}-oac",
            description=f"OAC for {resource_name}",
            origin_access_control_origin_type="s3",
            signing_behavior="always",
            signing_protocol="sigv4"
        )

        bucket = S3.create_bucket(
            name=f"{resource_name}",
            cors_rules=s3_cors_rules,
            tags=tags,
            block_public_access=True
        )

        s3_cloudfront = {
            "bucket": bucket,
            "origin_access_control": origin_access_control
        }

        return s3_cloudfront
