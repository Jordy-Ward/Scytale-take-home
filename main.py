import os
from dotenv import load_dotenv
from extract import GitHubClient, extract_pr_data

OWNER = "home-assistant"
REPO = "frontend"
SINCE = "2026-11-01T00:00:00Z"
MAX_PRS = None

def main():
    load_dotenv()
    token = os.environ["GITHUB_TOKEN"]
    client = GitHubClient(token)
    
    # extract
    extract_pr_data(client, OWNER, REPO, SINCE, MAX_PRS)
    # transform
    
    # load
    
if __name__ == "__main__":
    main()