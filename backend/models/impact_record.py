# backend/models/impact_record.py
"""
ImpactRecord model — stores results of regulation change propagation analysis.
NEW in v3 (Module 5).
"""

import uuid
from datetime import datetime, timezone

from backend.extensions import db


class ImpactRecord(db.Model):
    """
    One impact entry produced by the Change Propagation Agent.

    When a new circular is ingested, the propagation agent traverses
    the temporal graph to find every affected obligation, process,
    and contract template. Each affected item generates one ImpactRecord.
    """

    __tablename__ = "impact_records"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_circular_id = db.Column(
        db.String(36),
        db.ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        comment="The new circular that triggered the impact analysis",
    )
    source_circular_ref = db.Column(
        db.String(100),
        nullable=False,
        comment="Circular reference (e.g., 2025-03) for quick display",
    )
    affected_entity_type = db.Column(
        db.String(50),
        nullable=False,
        comment="obligation | process | contract_template | circular",
    )
    affected_entity_id = db.Column(
        db.String(100),
        nullable=False,
        comment="Neo4j node ID or reference of the affected entity",
    )
    affected_entity_name = db.Column(
        db.String(500),
        comment="Human-readable name of the affected entity",
    )
    severity = db.Column(
        db.String(20),
        nullable=False,
        comment="LOW | MEDIUM | HIGH | CRITICAL",
    )
    impact_description = db.Column(
        db.Text,
        comment="LLM-generated description of the impact",
    )
    relationship_path = db.Column(
        db.Text,
        comment="JSON-serialized path from source circular to affected entity",
    )
    is_acknowledged = db.Column(
        db.Boolean,
        default=False,
        comment="Whether a compliance officer has reviewed this impact",
    )
    acknowledged_by = db.Column(db.String(36), nullable=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
