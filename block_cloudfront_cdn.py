import pulumi_aws as aws

from aws_cloudfront import Cloudfront

class CDN:
    @staticmethod
    def create_cdn(prefix, project_name, environment, certificate, origins, log_bucket, aliases, behaviors, price_class, tags):

        resource_name = f"{prefix}{project_name}"

        certificate_viewer = aws.cloudfront.DistributionViewerCertificateArgs(
            acm_certificate_arn=certificate,
            minimum_protocol_version="TLSv1.2_2021",
            ssl_support_method="sni-only",
        )

        cdn_origins = []
        for origin in origins:
            if origin["type"] == "alb":
                dict = aws.cloudfront.DistributionOriginArgs(
                    custom_origin_config=aws.cloudfront.DistributionOriginCustomOriginConfigArgs(
                        http_port=80,
                        https_port=443,
                        origin_protocol_policy="https-only",
                        origin_ssl_protocols=[
                            "TLSv1",
                            "TLSv1.1",
                            "TLSv1.2",
                        ],
                    ),
                    domain_name=origin["dns"],
                    origin_id=f"{origin['type']}-{resource_name}-{origin['name']}",
                    origin_shield=aws.cloudfront.DistributionOriginOriginShieldArgs(
                        enabled=origin['origin_shield_enabled'],
                        origin_shield_region=origin['origin_shield_region'],
                    ),
                )
                cdn_origins.append(dict)
            elif origin["type"] == "s3":
                dict = aws.cloudfront.DistributionOriginArgs(
                    domain_name=origin["dns"],
                    origin_id=f"{origin['type']}-{resource_name}-{origin['name']}",
                    s3_origin_config=aws.cloudfront.DistributionOriginS3OriginConfigArgs(
                        origin_access_identity=origin["access_identity"],
                    ),
                )
                cdn_origins.append(dict)

        logging_config = aws.cloudfront.DistributionLoggingConfigArgs(
            bucket=log_bucket,
            include_cookies=True,
            prefix=f"{project_name}/{environment}/",
        )

        restrictions = aws.cloudfront.DistributionRestrictionsArgs(
            geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
                restriction_type="none",
            ),
        )

        distribution = Cloudfront.create_distribution(
            name=resource_name,
            aliases=aliases,
            viewer_certificate=certificate_viewer,
            enabled=True,
            price_class=price_class,
            origins=cdn_origins,
            custom_error_responses=behaviors["custom_responses"],
            default_cache_behavior=behaviors["default"],
            ordered_cache_behaviors=behaviors["ordered"],
            logging_config=logging_config,
            restrictions=restrictions,
            tags=tags
        )

        return distribution.domain_name
