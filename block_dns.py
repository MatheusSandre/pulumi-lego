import pulumi

from cloudflare_dns import DNS as CF_DNS
from aws_route53 import Route53

class DNS:
    @staticmethod
    def create_resources(app_url, cf_zone_id, route53_zone_id, dns_type, dns_value):

        CF_DNS.create_record(
            name=app_url,
            zone_id=cf_zone_id,
            value=dns_value,
            record_type=dns_type,
            proxied=True
        )

        if route53_zone_id:
            Route53.create_record(
                name=app_url,
                records=[f"{app_url}.cdn.cloudflare.net"],
                record_type=dns_type,
                ttl=60,
                zone_id=route53_zone_id
            )

        pulumi.export("app_url", app_url)
