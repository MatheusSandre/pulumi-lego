from aws_ssm import SSM

class Parameters:
    @staticmethod
    def create_parameters(project_name, account_id, environment, region, parameter_key,values):

        for value in values:
            SSM.create_parameter(
                name=f"/{project_name}/{environment}/{value['name']}",
                parameter_type="SecureString",
                key_id=parameter_key,
                value=value['value']
            )

        secrets = []

        for value in values:
            secret = {
                "valueFrom": f"arn:aws:ssm:{region}:{account_id}:parameter/{project_name}/{environment}/{value['name']}",
                "name": value['name']
            }

            secrets.append(secret)

        return secrets
