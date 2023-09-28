from setuptools import setup
# List of requirements
requirements = []  # This could be retrieved from requirements.txt
# Package (minimal) configuration
setup(
    name="lego",
    version="0.0.1",
    description="block resources",
    py_modules=["block_alb_ecs_service", "block_cloudfront_cdn", "block_dns", "block_ecs_cluster", "block_lambda_functions_go",
                "block_load_balancer", "block_memcached", "block_opensearch", "block_redis_cluster", "block_redis", "block_s3_cloudfront",
                "block_sqs_queues", "block_ssm", "block_worker_ecs_service"],
    #packages=find_packages(),  # __init__.py folders search
    install_requires=requirements
)
