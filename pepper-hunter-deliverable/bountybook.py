import socket
from datetime import datetime, timezone

def check_bountybook_domain(domain="api.bountybook.ai", timeout=3.0):
    """
    Checks if the BountyBook API domain is resolvable via DNS.
    Returns True if resolvable, False if NXDOMAIN or unreachable (temporary network failure).
    """
    original_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        socket.gethostbyname(domain)
        return True
    except (socket.gaierror, socket.timeout):
        return False
    finally:
        socket.setdefaulttimeout(original_timeout)

def process_bountybook_item(item):
    """
    Processes a BountyBook item. If the API domain fails DNS resolution,
    record the DNS failure reason/time without forcing a permanent close,
    but ensure claims_open is set to false if unreachable during the snapshot.
    """
    domain = "api.bountybook.ai"
    is_resolvable = check_bountybook_domain(domain)
    
    # Preserve historical record and payout label
    item.setdefault("_jobbi", {})
    item["_jobbi"]["source"] = "bountybook"
    
    if not is_resolvable:
        item["_jobbi"]["claims_open"] = False
        item["_jobbi"]["dns_status"] = "NXDOMAIN_OR_TIMEOUT"
        item["_jobbi"]["dns_checked_at"] = datetime.now(timezone.utc).isoformat()
    else:
        # Respect original claim status if domain is healthy
        pass
        
    return item
