import os
from dotenv import load_dotenv
from extract import GitHubClient, fetch_merged_prs
from utils import save_json

OWNER = "home-assistant"
REPO = "frontend"
SINCE = "2026-11-01T00:00:00Z"
MAX_PRS = None

def main():
    load_dotenv()
    token = os.environ["GITHUB_TOKEN"]
    client = GitHubClient(token)
    
    # Extract
    prs = fetch_merged_prs(client, "home-assistant", "frontend", "2026-11-01T00:00:00Z", max_prs=None)
    print("Merged PRs fetched:", len(prs))
    save_json(prs, "output/extract/pull_requests.json")
    
    # Transform
    
    # Load
    
if __name__ == "__main__":
    main()