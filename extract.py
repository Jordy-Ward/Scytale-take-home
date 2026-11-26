import time
import requests
from utils import save_json

API_URL = "https://api.github.com"

class GitHubClient:
    """Handle authentication, rate limits and pagination for GitHub REST API
       Create a reusable http session and add the token to its authorisation headers  
    """
    
    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers.update({
           "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", 
        })
        
    
    def get(self, url, params=None):
        """GET a URL, wait and retry if we hit the rate limit

        Args:
            url (str): URL to send the GET request to.
            params (dict, optional): Query parameters to include in the request. Defaults to None.

        Returns:
            requests.Response: Successful response for the requested page.
        """
        
        while True:
            resp = self.session.get(url, params=params, timeout=30)
            
            if resp.status_code in (403, 429) and resp.headers.get("X-RateLimit-Remaining") == "0":
                reset_at = int(resp.headers["X-RateLimit-Reset"])
                wait = max(reset_at - time.time(), 0) + 1
                print(f"Rate limit hit, sleeping {wait:.1f}s...")
                time.sleep(wait)
                continue
                
            resp.raise_for_status()
            return resp
        
    def paginate(self, url, params=None):
        """Yield every item across all pages of a list endpoint

        Args:
            url (str): URL of the list endpoint to request.
            params (dict, optional): Query parameters for the first page. Defaults to None.

        Returns:
            Generator: Items from all pages, yielded one at a time.
        """
        
        while url:
            resp = self.get(url, params)
            yield from resp.json()
            url = resp.links.get("next", {}).get("url")
            params = None
        
def fetch_merged_prs(client, owner, repo, since, max_prs=None):
    """Return merged prs as raw json, merged on or after `since`

    Args:
        client (GithubClient): Authenticated client used to request pull requests.
        owner (str): GitHub username or organization that owns the repository.
        repo (str): Repository name.
        since (str): ISO 8601 timestamp; only pull requests merged on or after it are returned.
        max_prs (int, optional): Maximum number of pull requests to return. Defaults to None (no limit).

    Returns:
        list: Pull request data for merged pull requests on or after `since`.
    """
    url = f"{API_URL}/repos/{owner}/{repo}/pulls"
    params = {"state": "closed", "sort": "updated", "direction": "desc", "per_page": 100}
    
    merged = []
    for pr in client.paginate(url, params):
        if pr["updated_at"] < since:
            break
        if pr["merged_at"] is None:
            continue
        if pr["merged_at"] < since:
            continue
        
        merged.append(pr)
        
        if max_prs and len(merged) >= max_prs:
            break
        
    return merged


def extract_pr_data(client, owner, repo, since, max_prs=None, out_dir="output/extract"):
    """Fetch merged PRs plus their reviews, checks and target branch rules, and save raw JSON

    Args:
        client (_type_): _description_
        owner (_type_): _description_
        repo (_type_): _description_
        since (_type_): _description_
        max_prs (_type_, optional): _description_. Defaults to None.
        out_dir (str, optional): _description_. Defaults to "output/extract".
    """
    prs = fetch_merged_prs(client, owner, repo, since, max_prs)
    print("Merged PRs fetched:", len(prs))
    
    reviews = {}
    check_runs = {}
    statuses = {}
    
    for i, pr in enumerate(prs, start=1):
        number = pr["number"]
        sha = pr["head"]["sha"]
        print(f"[{i}/{len(prs)}] PR #{number}")
        
        reviews[number] = fetch_reviews(client, owner, repo, number)
        check_runs[number] = fetch_check_runs(client, owner, repo, sha)
        statuses[number] = fetch_statuses(client, owner, repo, sha)
        
    base_branch_names = set()
    for pr in prs:
        base_branch_names.add(pr["base"]["ref"])
        
    branches = {}
    for branch_name in base_branch_names:
        try:
            branches[branch_name] = fetch_branch(client, owner, repo, branch_name)
        except requests.HTTPError as e:
            if e.response.status_code != 404:
                raise # unexpected error, throw it
            else:     
                branches[branch_name] = None # branch was not found, deleted after merge

    
    save_json(prs, f"{out_dir}/pull_requests.json")
    save_json(reviews, f"{out_dir}/reviews.json")
    save_json(check_runs, f"{out_dir}/check_runs.json")
    save_json(statuses, f"{out_dir}/statuses.json")
    save_json(branches, f"{out_dir}/branches.json")


# helper functions
def fetch_reviews(client, owner, repo, pr_number):
    url = f"{API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    resp = client.get(url, params={"per_page": 100})
    return resp.json()

def fetch_check_runs(client, owner, repo, sha):
    url = f"{API_URL}/repos/{owner}/{repo}/commits/{sha}/check-runs"
    resp = client.get(url, params={"per_page": 100})
    return resp.json()["check_runs"]

def fetch_statuses(client, owner, repo, sha):
    """Return commit statuses (the older CI reporting system) for one commit."""
    url = f"{API_URL}/repos/{owner}/{repo}/commits/{sha}/status"
    resp = client.get(url, params={"per_page": 100})
    return resp.json()["statuses"]

def fetch_branch(client, owner, repo, branch):
    """Return a branch's details, including its protection rules (required checks)."""
    url = f"{API_URL}/repos/{owner}/{repo}/branches/{branch}"
    return client.get(url).json()

    