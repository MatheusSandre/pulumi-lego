from aws_ec2 import EC2
from aws_elasticache import Elasticache

class Memcached:
    @staticmethod
    def create_resource(prefix, service_name, project_name, environment, vpc, engine_version, node_type, nodes, parameter_group):
        tags = {
            "Environment": environment,
            "Service": service_name
        }
        resource_name = f"{prefix}{project_name}"

        memcached_subnet_group = Elasticache.create_subnet_group(
            name=f"{resource_name}-memcached",
            subnet_ids=vpc["publicSubnetIDs"],
        )

        memcached_sg = EC2.create_security_group(
            name=f"{resource_name}-memcached-sg",
            vpc_id=vpc["vpcID"],
            tags=tags,
        )

        EC2.create_sg_rule(
            name=f"{resource_name}-memcached-access",
            security_group_id=memcached_sg,
            from_port=0,
            to_port=0,
            protocol=-1,
            rule_type="ingress",
            is_self=True,
        )

        EC2.create_sg_rule(
            name=f"{resource_name}-memcached-out-access",
            security_group_id=memcached_sg,
            from_port=0,
            to_port=0,
            protocol=-1,
            rule_type="egress",
            cidr_blocks=["0.0.0.0/0"],
        )

        Elasticache.create_cluster(
            name=resource_name,
            engine="memcached",
            engine_version=engine_version,
            node_type=node_type,
            num_cache_nodes=nodes,
            port=11211,
            parameter_group_name=parameter_group,
            az_mode="single-az",
            subnet_group_name=memcached_subnet_group,
            security_group_ids=[memcached_sg],
            tags=tags,
        )

        memcached_dns = str(Elasticache.get_cluster(
            name=f"{prefix}{project_name}").cluster_address)

        memcached_values = {
            "sg": memcached_sg,
            "dns": f"{memcached_dns}:11211"
        }

        return memcached_values
