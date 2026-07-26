"""
Shared audit-logging helper. Every access to sensitive data (esp. Patient
and Medical Records services) should call `write_audit_log` so the platform
can answer "who accessed patient data, when, what action, from where" per
the compliance requirements.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

audit_logger = logging.getLogger("medicore.audit")


def write_audit_log(
    *,
    actor_id: str,
    actor_role: str,
    action: str,
    resource_type: str,
    resource_id: str,
    source_ip: Optional[str] = None,
    outcome: str = "SUCCESS",
    metadata: Optional[dict] = None,
) -> None:
    """
    Emits a structured JSON audit event to stdout, which is scraped by
    Promtail -> Loki -> Grafana in the platform's observability stack, and
    additionally shipped to CloudWatch/OpenSearch for compliance retention.
    """
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor_id": actor_id,
        "actor_role": actor_role,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "source_ip": source_ip,
        "outcome": outcome,
        "metadata": metadata or {},
    }
    audit_logger.info(json.dumps(event))
