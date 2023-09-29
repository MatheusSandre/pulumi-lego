from aws_ec2 import EC2
from aws_alb import LoadBalancer as AwsLoadBalancer

class LoadBalancer:
    @staticmethod
    def create_lb(prefix, service_name, project_name, environment, is_internal, vpc, certificate_arn, health_check_path, app_port, tags):

        resource_name = f"{prefix}{service_name}"

        alb_sg = EC2.create_security_group(
            name=f"alb-{resource_name}-sg",
            vpc_id=vpc["vpcID"],
            tags=tags
        )

        EC2.create_sg_rule(
            name=f"alb-{resource_name}-sg-ingress",
            security_group_id=alb_sg,
            from_port=443,
            to_port=443,
            protocol="tcp",
            rule_type="ingress",
            cidr_blocks=["0.0.0.0/0"]
        )

        EC2.create_sg_rule(
            name=f"alb-{resource_name}-sg-egress",
            security_group_id=alb_sg,
            from_port=0,
            to_port=0,
            protocol="-1",
            rule_type="egress",
            cidr_blocks=["0.0.0.0/0"]
        )

        if is_internal:
            subnets = "privateSubnetIDs"
        else:
            subnets = "publicSubnetIDs"

        _alb = AwsLoadBalancer.create_load_balancer(
            name=f"alb-{resource_name}",
            load_balancer_type="application",
            is_internal=is_internal,
            ip_address_type="ipv4",
            security_groups=[alb_sg],
            idle_timeout=60,
            subnets=vpc[subnets],
            tags=tags
        )

        tg_health_check = {
            "enabled": True,
            "healthy_threshold": 5,
            "interval": 30,
            "matcher": "200",
            "path": health_check_path,
            "port": app_port,
            "protocol": "HTTP",
            "timeout": 5,
            "unhealthy_threshold": 2
        }

        target_group = AwsLoadBalancer.create_target_group(
            name=f"{resource_name}",
            health_check=tg_health_check,
            deregistration_delay=5,
            target_type="ip",
            port=app_port,
            protocol="HTTP",
            vpc_id=vpc["vpcID"],
        )

        AwsLoadBalancer.create_listener(
            name=f"{resource_name}_lb_listener",
            certificate_arn=certificate_arn,
            ssl_policy="ELBSecurityPolicy-TLS-1-2-Ext-2018-06",
            load_balancer_arn=_alb.arn,
            port=443,
            protocol="HTTPS",
            default_actions=[{
                "type": "forward",
                "target_group_arn": target_group.arn
            }],
        )

        values = {
            "target_group": target_group.arn,
            "alb_sg": alb_sg.id,
            "alb_dns": _alb.dns_name
        }

        return values
