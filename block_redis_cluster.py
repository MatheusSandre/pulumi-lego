from aws_ec2 import EC2
from aws_elasticache import Elasticache

class Redis:
    @staticmethod
    def create_resource(prefix, redis_name, service_name, project_name, environment, vpc, engine_version, node_type, num_nodes, num_replicas, parameter_group, tags):

        resource_name = f"{prefix}{project_name}"

        redis_subnet_group = Elasticache.create_subnet_group(
            name=f"{resource_name}-redis",
            subnet_ids=vpc["publicSubnetIDs"],
        )

        redis_sg = EC2.create_security_group(
            name=f"{resource_name}-redis-sg",
            vpc_id=vpc["vpcID"],
            tags=tags,
        )

        EC2.create_sg_rule(
            name=f"{resource_name}-redis-access",
            security_group_id=redis_sg,
            from_port=0,
            to_port=0,
            protocol=-1,
            rule_type="ingress",
            is_self=True,
        )

        EC2.create_sg_rule(
            name=f"{resource_name}-redis-out-access",
            security_group_id=redis_sg,
            from_port=0,
            to_port=0,
            protocol=-1,
            rule_type="egress",
            cidr_blocks=["0.0.0.0/0"],
        )

        redis = Elasticache.create_replication(
            name=f"{resource_name}-{redis_name}",
            engine="redis",
            engine_version=engine_version,
            num_node_groups=num_nodes,
            replicas_per_node_group=num_replicas,
            automatic_failover_enabled=True,
            node_type=node_type,
            port=6379,
            parameter_group_name=parameter_group,
            subnet_group_name=redis_subnet_group,
            security_group_ids=[redis_sg],
            tags=tags,
        )

        redis_values = {
            "sg": redis_sg,
            "redis": redis
        }

        return redis_values
