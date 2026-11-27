import os
from dotenv import load_dotenv
from extract import GitHubClient, extract_pr_data
from transform import transform_pr_data
from utils import save_csv

OWNER = "home-assistant"
REPO = "frontend"
SINCE = "2026-11-01T00:00:00Z"
MAX_PRS = None

def main():
    load_dotenv()
    token = os.environ["GITHUB_TOKEN"]
    client = GitHubClient(token)
    
    # extract
    # extract_pr_data(client, OWNER, REPO, SINCE, MAX_PRS)
    
    # transform
    rows = transform_pr_data()

    print("CR passed:", sum(row["CR_Passed"] for row in rows), "of", len(rows))
    print("Checks passed:", sum(row["CHECKS_PASSED"] for row in rows), "of", len(rows))
    
    # load
    save_csv(rows, "output/report/pr_report.csv")
    print(f"Report written. # PRs: {len(rows)}")
    
if __name__ == "__main__":
    main()