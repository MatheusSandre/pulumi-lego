import json
from aws_sqs import SQS


class Queues:
    @staticmethod
    def create_queues(prefix, service_name, project_name, environment, queues):
        tags = {
            "Environment": environment,
            "Service": service_name
        }
        resource_name = f"{prefix}{project_name}"

        resources=[]
        for queue_name, attr in queues.items():
            dlq_queue = SQS.create_queue(
                name=f"{resource_name}-{queue_name}-deadletter",
                message_retention_seconds=attr.get(
                    "messageRetentionSeconds", 60),
                visibility_timeout_seconds=attr.get(
                    "visibilityTimeoutSeconds", 10),
                tags=tags
            )
            queue = SQS.create_queue(
                name=f"{resource_name}-{queue_name}",
                message_retention_seconds=attr.get(
                    "messageRetentionSeconds", 60),
                visibility_timeout_seconds=attr.get(
                    "visibilityTimeoutSeconds", 10),
                tags=tags,
                depends_on=[dlq_queue]
            )

            SQS.create_redrive_policy(
                name=f"{resource_name}-{queue_name}",
                queue_url=queue.id,
                redrive_policy=dlq_queue.arn.apply(
                    lambda arn: json.dumps({
                        "deadLetterTargetArn": arn,
                        "maxReceiveCount": 4,
                    })
                )
            )

            SQS.create_redrive_allow_policy(
                name=f"{resource_name}-{queue_name}",
                queue_url=dlq_queue.id,
                redrive_allow_policy=queue.arn.apply(
                    lambda arn: json.dumps({
                        "redrivePermission": "byQueue",
                        "sourceQueueArns": [arn],
                    })
                )
            )

            dict = {
                "name": queue_name,
                "queue": queue,
                "deadletter": dlq_queue
            }
            resources.append(dict)

        return resources
