"""
Cryptographic Tamper-Evident SHA-256 Audit Hash Chain for KUSOR.
Ensures non-repudiation and tamper-proofing of all AI regulatory responses,
compliance screenings, and administrative actions for Internal Audit and BCT inspections.
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

GENESIS_PREV_HASH = "0" * 64
AUDIT_LOG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/audit_chain.jsonl"))

class AuditHashChain:
    """
    Manages a continuous append-only cryptographic hash chain.
    Every record contains SHA-256(sequence | timestamp | actor | action | payload_hash | response_hash | prev_hash).
    """

    def __init__(self, log_path: str = AUDIT_LOG_FILE):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        if not os.path.exists(self.log_path):
            self._create_genesis_block()

    def _hash_string(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _create_genesis_block(self) -> Dict[str, Any]:
        genesis = {
            "sequence": 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "actor_id": "SYSTEM",
            "action": "GENESIS_INITIALIZATION",
            "payload_hash": self._hash_string("KUSOR_AUDIT_CHAIN_GENESIS"),
            "response_hash": self._hash_string("INITIALIZED"),
            "sources_cited": [],
            "prev_hash": GENESIS_PREV_HASH,
        }
        computed_hash = self._compute_block_hash(genesis)
        genesis["block_hash"] = computed_hash

        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(genesis) + "\n")
        return genesis

    def _compute_block_hash(self, block: Dict[str, Any]) -> str:
        payload = (
            f"{block['sequence']}|"
            f"{block['timestamp']}|"
            f"{block.get('actor_id', 'ANON')}|"
            f"{block['action']}|"
            f"{block['payload_hash']}|"
            f"{block['response_hash']}|"
            f"{block['prev_hash']}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get_latest_block(self) -> Dict[str, Any]:
        if not os.path.exists(self.log_path):
            return self._create_genesis_block()
        
        last_line = None
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last_line = line.strip()
        
        if not last_line:
            return self._create_genesis_block()
        return json.loads(last_line)

    def seal_event(
        self,
        action: str,
        actor_id: str = "SYSTEM",
        payload: Any = None,
        response: Any = None,
        sources_cited: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Appends and seals a new event into the cryptographic audit chain.
        """
        latest = self.get_latest_block()
        prev_hash = latest["block_hash"]
        sequence = latest["sequence"] + 1

        payload_str = json.dumps(payload, sort_keys=True) if payload else ""
        response_str = json.dumps(response, sort_keys=True) if response else ""

        block = {
            "sequence": sequence,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "actor_id": str(actor_id),
            "action": action,
            "payload_hash": self._hash_string(payload_str),
            "response_hash": self._hash_string(response_str),
            "sources_cited": sources_cited or [],
            "prev_hash": prev_hash,
        }
        block["block_hash"] = self._compute_block_hash(block)

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(block) + "\n")

        return block

    def verify_chain_integrity(self) -> Tuple[bool, int, List[int]]:
        """
        Verifies the cryptographic integrity of the entire audit chain.
        Returns: (is_valid, total_blocks, list_of_corrupted_sequence_numbers)
        """
        if not os.path.exists(self.log_path):
            return True, 0, []

        blocks = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    blocks.append(json.loads(line.strip()))

        if not blocks:
            return True, 0, []

        corrupted = []
        expected_prev_hash = GENESIS_PREV_HASH

        for idx, block in enumerate(blocks):
            if block["prev_hash"] != expected_prev_hash:
                corrupted.append(block["sequence"])

            recalculated = self._compute_block_hash(block)
            if recalculated != block["block_hash"]:
                if block["sequence"] not in corrupted:
                    corrupted.append(block["sequence"])

            expected_prev_hash = block["block_hash"]

        is_valid = len(corrupted) == 0
        return is_valid, len(blocks), corrupted

    def get_recent_blocks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns the most recent N blocks from the audit chain."""
        if not os.path.exists(self.log_path):
            return []
        
        blocks = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    blocks.append(json.loads(line.strip()))
        return list(reversed(blocks[-limit:]))

# Singleton instance
audit_chain = AuditHashChain()
