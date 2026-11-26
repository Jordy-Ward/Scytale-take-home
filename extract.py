import time
import requests

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

def fetch_reviews(client, owner, repo, pr_number):
    url = f"{API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    resp = client.get(url, params={"per_page": 100})
    return resp.json()

def fetch_check_runs(client, owner, repo, sha):
    url = f"{API_URL}/repos/{owner}/{repo}/commits/{sha}/check-runs"
    resp = client.get(url, params={"per_page": 100})
    return resp.json()["check_runs"]
    