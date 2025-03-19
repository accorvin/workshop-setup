import os
import yaml

from jinja2 import Environment, FileSystemLoader
from kubernetes import client, config
from openshift.dynamic import DynamicClient

USERS_LIST_FILE = 'users_list.txt'
VARS_FILE = 'vars.yaml'
TEMPLATES = [
    'project.yaml.j2',
    'role-binding.yaml.j2',
    'persistent-volume-claim.yaml.j2',
    'workbench.yaml.j2',
    'data-initialization-script-configmap.yaml.j2',
    'data-initialization-credentials-secret.yaml.j2'
]


def get_variables():
    pass


def render_templates(variables, username, template_name):
    # Define the directory containing the template files
    template_dir = 'templates'  # Change this to the directory containing your templates

    # Create a Jinja2 environment and load templates from the directory
    env = Environment(loader=FileSystemLoader(template_dir))

    # Load the template by its file name
    template = env.get_template(template_name)

    # Define the variables to pass to the template
    username_short = username[:12]
    variables.update({
        'username_short': username_short,
        'username': username,
        'project': f'{username_short}-workshop',
        'workbench_name': f'{username_short}-workshop'
    })

    # Render the template with the variables
    rendered_output = template.render(variables)

    return rendered_output


def main():
    config.load_kube_config()
    dyn_client = DynamicClient(client.ApiClient())
    with open(USERS_LIST_FILE) as f:
        workshop_participants = f.readlines()

    with open(VARS_FILE) as f:
        variables = yaml.safe_load(f.read())

    variables['s3_key'] = os.environ['S3_KEY']
    variables['s3_secret'] = os.environ['S3_SECRET']

    for user in workshop_participants:
        safe_username = user.lower().strip()
        print(f'Setting up environment for user {safe_username}')
        for template in TEMPLATES:
            template_data = render_templates(variables, safe_username, template)
            template_data_yaml = yaml.safe_load(template_data)
            object = dyn_client.resources.get(api_version=template_data_yaml['apiVersion'], kind=template_data_yaml['kind'])
            object.apply(body=template_data_yaml)



if __name__ == '__main__':
    main()