from jobbi.sources.bountybook import process_bountybook_item
from jobbi.sources.algora import process_algora_item

def enrich_and_filter_claims(items):
    """
    Iterates through feed items, applying source-specific validation rules
    to separate board-reported open state from currently usable submission paths.
    Keeps healthy sources as positive controls.
    """
    processed_items = []
    
    for item in items:
        jobbi_meta = item.get("_jobbi", {})
        source = jobbi_meta.get("source")
        
        if source == "bountybook":
            item = process_bountybook_item(item)
        elif source == "algora" or jobbi_meta.get("extra", {}).get("repo"):
            item = process_algora_item(item)
        else:
            # Positive control / healthy sources pass through cleanly
            pass
            
        processed_items.append(item)
        
    return processed_items
