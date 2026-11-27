from utils import load_json





def transform_pr_data(in_dir="output/extract"):
    """Build one report row per merged pull request from raw extract data files

    Args:
        in_dir (str, optional): _description_. Defaults to "output/extract".
    """
    prs = load_json(f"{in_dir}/pull_requests.json")
    reviews = load_json(f"{in_dir}/reviews.json")
    check_runs = load_json(f"{in_dir}/check_runs.json")
    statuses = load_json(f"{in_dir}/statuses.json")
    branches = load_json(f"{in_dir}/branches.json")
    
    rows = []
    for pr in prs:
        number = str(pr["number"])
        pr_reviews = reviews.get(number, [])
        user = pr.get("user")
        branch = branches.get(pr["base"]["ref"]) or {}
        required_checks = branch.get("protection", {}).get("required_status_checks", {}).get("contexts", [])

        checks_passed = all(
            is_check_passed(name, check_runs.get(number, []), statuses.get(number, []), pr["merged_at"])
            for name in required_checks
        )
        row = {
            "pr_number": pr["number"],
            "title": pr["title"],
            "author": user["login"] if user else None,
            "merged_at": pr["merged_at"],
            "CR_Passed": is_review_passed(pr_reviews, pr["merged_at"]),
            "CHECKS_PASSED": checks_passed, 
        }
        rows.append(row)

    return rows

def is_check_passed(name, check_runs, statuses, merged_at):
    """True if the named check succeeded before the merge, in either CI system."""
    for run in check_runs:
        if run["name"] == name and run["conclusion"] == "success" and run["completed_at"] <= merged_at:
            return True
    for status in statuses:
        if status["context"] == name and status["state"] == "success" and status["updated_at"] <= merged_at:
            return True
    return False

def is_review_passed(reviews, merged_at):
    """True if at least one human approved the PR before it was merged."""
    for review in reviews:
        if review["state"] != "APPROVED":
            continue                                  # comments, dismissed, changes requested
        if review["user"] is None or review["user"]["type"] == "Bot":
            continue                                  # bots don't count as code review
        if review["submitted_at"] > merged_at:
            continue                                  # approved after the merge, too late
        return True                                   # found a valid approval
    return False