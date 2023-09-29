import pulumi

from aws_cloudwatch import Cloudwatch
from aws_opensearch import Opensearch as AWSOpensearch
from cloudflare_dns import DNS as CF_DNS
from aws_route53 import Route53

config = pulumi.Config()

class Opensearch:
    @staticmethod
    def create_domain(prefix, service_name, project_name, environment, cluster_config, engine_version,
                      cognito_options, ebs_options, logs_enabled, custom_endpoint,
                      custom_endpoint_certificate_arn, custom_endpoint_enabled, cf_zone_id,
                      route53_zone_id, dns_type, tags):

        resource_name = f"{prefix}{service_name}"

        search_logs = Cloudwatch.create_log_group(f"/aws/aes/domains/{resource_name}/search-logs")

        app_logs = Cloudwatch.create_log_group(f"/aws/aes/domains/{resource_name}/application-logs")

        index_logs = Cloudwatch.create_log_group(f"/aws/aes/domains/{resource_name}/index-logs")

        domain_endpoint_options = {
                "custom_endpoint": custom_endpoint,
                "custom_endpoint_certificate_arn": custom_endpoint_certificate_arn,
                "custom_endpoint_enabled": custom_endpoint_enabled,
                "enforceHttps": False,
                "tls_security_policy": "Policy-Min-TLS-1-0-2019-07"
            }

        opensearch = AWSOpensearch.create_domain(
            name=resource_name,
            engine_version=engine_version,
            cluster_config=cluster_config,
            cognito_options=cognito_options,
            log_publishing_options=[
                {
                    "cloudwatchLogGroupArn": search_logs.arn,
                    "enabled": logs_enabled,
                    "logType": "SEARCH_SLOW_LOGS"
                },
                {
                    "cloudwatchLogGroupArn": app_logs.arn,
                    "enabled": logs_enabled,
                    "logType": "ES_APPLICATION_LOGS"
                },
                {
                    "cloudwatchLogGroupArn": index_logs.arn,
                    "enabled": logs_enabled,
                    "logType": "INDEX_SLOW_LOGS"
                }
            ],
            ebs_options=ebs_options,
            domain_endpoint_options=domain_endpoint_options,
            tags=tags,
        )

        CF_DNS.create_record(
            name=custom_endpoint,
            zone_id=cf_zone_id,
            value=opensearch.endpoint,
            record_type=dns_type,
            proxied=False
        )

        if route53_zone_id:
            Route53.create_record(
                name=custom_endpoint,
                records=[f"{custom_endpoint}.cdn.cloudflare.net"],
                record_type="CNAME",
                ttl=60,
                zone_id=route53_zone_id
            )

        dns = f"https://{custom_endpoint}"

        opensearch_values = {
            "dns": dns,
            "url": custom_endpoint,
            "opensearch": opensearch
        }

        return opensearch_values
