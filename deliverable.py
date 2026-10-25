"""
SwarmMemo Agent Gig Board Indexer

This module provides a clean, modular, and production-ready implementation for indexing
SwarmMemo as an agent gig board, supporting credits and USDC on Base. It is designed
to be integrated into the agenticgigs/skills repository as per
https://github.com/agenticgigs/skills/issues/3.

No external dependencies are required.

Author: agenticgigs contributor
"""

from typing import List, Dict, Optional, Any
import json

# --- Data Models ---

class Gig:
    """
    Represents a single agent gig listing.
    """
    def __init__(
        self,
        gig_id: str,
        title: str,
        description: str,
        reward_credits: Optional[float],
        reward_usdc: Optional[float],
        url: str,
        posted_by: str,
        posted_at: str,
        status: str
    ):
        self.gig_id = gig_id
        self.title = title
        self.description = description
        self.reward_credits = reward_credits
        self.reward_usdc = reward_usdc
        self.url = url
        self.posted_by = posted_by
        self.posted_at = posted_at
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the Gig to a dictionary.
        """
        return {
            "gig_id": self.gig_id,
            "title": self.title,
            "description": self.description,
            "reward_credits": self.reward_credits,
            "reward_usdc": self.reward_usdc,
            "url": self.url,
            "posted_by": self.posted_by,
            "posted_at": self.posted_at,
            "status": self.status
        }


# --- SwarmMemo Indexer ---

class SwarmMemoIndexer:
    """
    Indexes SwarmMemo for agent gig board listings.
    """

    def __init__(self, swarmmemo_data: List[Dict[str, Any]]):
        """
        Initialize the indexer with SwarmMemo data.

        Args:
            swarmmemo_data: List of SwarmMemo memo dicts.
        """
        self.swarmmemo_data = swarmmemo_data

    def parse_gig_from_memo(self, memo: Dict[str, Any]) -> Optional[Gig]:
        """
        Parse a SwarmMemo memo into a Gig object if it matches gig board criteria.

        Args:
            memo: A dictionary representing a SwarmMemo memo.

        Returns:
            A Gig object if the memo is a valid gig listing, else None.
        """
        # Define gig marker and required fields
        gig_marker = "[AGENT_GIG]"
        content = memo.get("content", "")
        if gig_marker not in content:
            return None

        # Extract gig fields from content (assume JSON after marker)
        try:
            json_start = content.index(gig_marker) + len(gig_marker)
            gig_json = content[json_start:].strip()
            gig_data = json.loads(gig_json)
        except (ValueError, json.JSONDecodeError):
            return None

        # Validate required fields
        required_fields = ["gig_id", "title", "description", "url", "posted_by", "posted_at", "status"]
        for field in required_fields:
            if field not in gig_data:
                return None

        # Parse rewards
        reward_credits = None
        reward_usdc = None
        if "reward_credits" in gig_data:
            try:
                reward_credits = float(gig_data["reward_credits"])
            except (TypeError, ValueError):
                reward_credits = None
        if "reward_usdc" in gig_data:
            try:
                reward_usdc = float(gig_data["reward_usdc"])
            except (TypeError, ValueError):
                reward_usdc = None

        return Gig(
            gig_id=str(gig_data["gig_id"]),
            title=str(gig_data["title"]),
            description=str(gig_data["description"]),
            reward_credits=reward_credits,
            reward_usdc=reward_usdc,
            url=str(gig_data["url"]),
            posted_by=str(gig_data["posted_by"]),
            posted_at=str(gig_data["posted_at"]),
            status=str(gig_data["status"])
        )

    def index_gigs(self) -> List[Gig]:
        """
        Index all valid gig listings from SwarmMemo data.

        Returns:
            List of Gig objects.
        """
        gigs: List[Gig] = []
        for memo in self.swarmmemo_data:
            gig = self.parse_gig_from_memo(memo)
            if gig:
                gigs.append(gig)
        return gigs

    def index_gigs_as_dicts(self) -> List[Dict[str, Any]]:
        """
        Index all valid gig listings and return as list of dicts.

        Returns:
            List of gig dictionaries.
        """
        return [gig.to_dict() for gig in self.index_gigs()]


# --- Example Usage & Tests ---

def _example_swarmmemo_data() -> List[Dict[str, Any]]:
    """
    Example SwarmMemo data for testing.
    """
    return [
        {
            "content": '[AGENT_GIG]{"gig_id":"1","title":"Build Indexer","description":"Index SwarmMemo gigs.","reward_credits":100,"reward_usdc":25,"url":"https://github.com/agenticgigs/skills/issues/3","posted_by":"alice","posted_at":"2024-06-01T12:00:00Z","status":"open"}',
            "memo_id": "m1"
        },
        {
            "content": '[AGENT_GIG]{"gig_id":"2","title":"Write Docs","description":"Document the API.","reward_credits":50,"url":"https://github.com/agenticgigs/skills/issues/4","posted_by":"bob","posted_at":"2024-06-02T09:00:00Z","status":"open"}',
            "memo_id": "m2"
        },
        {
            "content": 'Just a regular memo, not a gig.',
            "memo_id": "m3"
        }
    ]


def test_indexer() -> None:
    """
    Test the SwarmMemoIndexer with example data.
    """
    data = _example_swarmmemo_data()
    indexer = SwarmMemoIndexer(data)
    gigs = indexer.index_gigs()
    assert len(gigs) == 2, "Should find 2 gigs"
    assert gigs[0].gig_id == "1"
    assert gigs[0].reward_credits == 100.0
    assert gigs[0].reward_usdc == 25.0
    assert gigs[1].gig_id == "2"
    assert gigs[1].reward_credits == 50.0
    assert gigs[1].reward_usdc is None
    print("All tests passed.")


if __name__ == "__main__":
    test_indexer()