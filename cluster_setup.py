import argparse
import os
import requests
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


def render_templates(variables, username, safe_username, template_name):
    # Define the directory containing the template files
    template_dir = 'templates'  # Change this to the directory containing your templates

    # Create a Jinja2 environment and load templates from the directory
    env = Environment(loader=FileSystemLoader(template_dir))

    # Load the template by its file name
    template = env.get_template(template_name)

    # Define the variables to pass to the template
    username_short = safe_username[:12]
    variables.update({
        'original_username': username,
        'username_short': username_short,
        'username': safe_username,
        'project': f'{username_short}-workshop',
        'workbench_name': f'{username_short}-workshop'
    })

    # Render the template with the variables
    rendered_output = template.render(variables)

    return rendered_output

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user')
    return parser.parse_args()


def get_github_user_id(github_token, headers, username):
    """Fetch the user ID of a GitHub username."""
    response = requests.get(f"https://api.github.com/users/{username}", headers=headers)
    
    if response.status_code == 200:
        user_data = response.json()
        return user_data["id"]
    elif response.status_code == 404:
        print(f"❌ User {username} not found.")
    else:
        print(f"❌ Failed to fetch user ID for {username}. Error: {response.text}")
    return None

def add_user_to_github_org(github_token, username):
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    github_org = 'ai-for-good-workshop'
    github_api_url = f"https://api.github.com/orgs/{github_org}/invitations"
    user_id = get_github_user_id(github_token, headers, username)
    response = requests.post(github_api_url, headers=headers, json={"invitee_id": user_id})
    
    if response.status_code == 201:
        print(f"✅ Successfully invited {username}")
    elif 'Over invitation rate limit' in response.text:
        print(f"❌ Failed to invite {username}. GitHub API Rate Limit hit {response.text}")
    elif response.status_code == 422:
        print(f"⚠️ {username} is already a member or has a pending invite.")
    elif response.status_code == 404:
        print(f"❌ User {username} not found. Check if the username exists.")
    else:
        print(f"❌ Failed to invite {username}. Error: {response.text}")


def setup_openshift_cluster(variables, dyn_client, user):
    safe_username = user.lower().strip()
    print(f'Setting up environment for user {safe_username}')
    for template in TEMPLATES:
        template_data = render_templates(variables, user.strip(), safe_username, template)
        template_data_yaml = yaml.safe_load(template_data)
        object = dyn_client.resources.get(api_version=template_data_yaml['apiVersion'], kind=template_data_yaml['kind'])
        object.apply(body=template_data_yaml)


def main():
    args = parse_args()
    if args.user:
        workshop_participants = [args.user]
    else:
        with open(USERS_LIST_FILE) as f:
            workshop_participants = f.readlines()

    with open('.github_token.txt') as f:
        github_token = f.read().strip()

    config.load_kube_config()
    dyn_client = DynamicClient(client.ApiClient())

    with open(VARS_FILE) as f:
        variables = yaml.safe_load(f.read())

    variables['s3_key'] = os.environ['S3_KEY']
    variables['s3_secret'] = os.environ['S3_SECRET']

    for user in workshop_participants:
        add_user_to_github_org(github_token, user)
        setup_openshift_cluster(variables, dyn_client, user)


if __name__ == '__main__':
    main()