import requests

# Configuration
with open('.github_token.txt') as f:
    GITHUB_TOKEN = f.read().strip()

GITHUB_ORG = "ai-for-good-workshop"  # Replace with your GitHub organization name
USERNAMES_FILE = "users_list.txt"  # File containing GitHub usernames, one per line

# GitHub API endpoint for inviting users to an organization
GITHUB_API_URL = f"https://api.github.com/orgs/{GITHUB_ORG}/invitations"

# Headers for authentication
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

def get_user_id(username):
    """Fetch the user ID of a GitHub username."""
    response = requests.get(f"https://api.github.com/users/{username}", headers=HEADERS)
    
    if response.status_code == 200:
        user_data = response.json()
        return user_data["id"]
    elif response.status_code == 404:
        print(f"❌ User {username} not found.")
    else:
        print(f"❌ Failed to fetch user ID for {username}. Error: {response.text}")
    return None

def invite_user(username):
    user_id = get_user_id(username)
    """Invite a GitHub user to the organization."""
    response = requests.post(GITHUB_API_URL, headers=HEADERS, json={"invitee_id": user_id})
    
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

def main():
    """Read usernames from file and send invites."""
    try:
        with open(USERNAMES_FILE, "r") as file:
            usernames = [line.strip() for line in file if line.strip()]

        for username in usernames:
            invite_user(username)
    except FileNotFoundError:
        print(f"❌ Error: The file {USERNAMES_FILE} was not found.")

if __name__ == "__main__":
    main()