import urllib.request
import json

def fetch_github_repo_status(repo_slug):
    """
    Fetches repository metadata from GitHub to check if it's archived or read-only.
    repo_slug e.g. 'rohitdash08/FinMind'
    """
    url = f"https://api.github.com/repos/{repo_slug}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Jobbi-Agent-Checker", "Accept": "application/vnd.github+json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=4.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                return {
                    "archived": data.get("archived", False),
                    "locked": False # Default repo level
                }
    except Exception:
        pass
    return {"archived": False, "locked": False}

def fetch_github_issue_status(repo_slug, issue_number):
    """
    Fetches specific issue metadata to check if it's locked or submission window closed.
    """
    url = f"https://api.github.com/repos/{repo_slug}/issues/{issue_number}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Jobbi-Agent-Checker", "Accept": "application/vnd.github+json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=4.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                return {
                    "state": data.get("state"),
                    "locked": data.get("locked", False)
                }
    except Exception:
        pass
    return {"state": "open", "locked": False}

def process_algora_item(item):
    """
    Validates Algora items against repository archive status and issue locks/deadlines.
    Explicit repository archive/lock or deadline should not produce claims_open:true.
    """
    extra = item.get("_jobbi", {}).get("extra", {})
    repo = extra.get("repo")
    
    item.setdefault("_jobbi", {})
    item["_jobbi"]["source"] = "algora"
    
    is_archived = False
    is_locked = False
    
    if repo:
        repo_status = fetch_github_repo_status(repo)
        is_archived = repo_status.get("archived", False)
        
        # Check issue if URL or reference exists
        url = item.get("url", "")
        if "issues/" in url:
            try:
                parts = url.rstrip("/").split("/")
                issue_num = int(parts[-1])
                issue_status = fetch_github_issue_status(repo, issue_num)
                is_locked = issue_status.get("locked", False)
                if issue_status.get("state") == "closed":
                    is_locked = True
            except ValueError:
                pass

    # Explicit repository archive/lock or deadline should not produce claims_open:true
    if is_archived or is_locked:
        item["_jobbi"]["claims_open"] = False
        item["_jobbi"]["archive_or_lock_override"] = True
        
    return item
