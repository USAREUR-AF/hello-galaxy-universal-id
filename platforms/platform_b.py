"""Platform B — cert/role-gated analytics service (stand-in for an invented
third-party vendor, "Acme Analytics").

Role-bound. It authorizes a dataset query off the descriptor's role/echelon
(and, in a live run, the cert CN it already verified). A reorg does not change
RAVEN-03's role, so its access here does NOT change — also correct. Different
platform, different binding, independently coherent.

Stand-in note: the role->access rule is illustrative; it models the consumption
pattern, not any product.
"""
from lib import descriptor

# datasets this service exposes, and which roles may query them
_POLICY = {
    "sensor-feeds": {"OPERATOR", "MONITOR", "ADMIN"},
    "admin-config": {"ADMIN"},
}


def authorize(desc, dataset, as_of=None):
    r = descriptor.role(desc)
    allowed = r in _POLICY.get(dataset, set())
    return {
        "platform": "B (analytics svc)",
        "binds_to": "grammar.role",
        "result": f"query '{dataset}' as role {r}: {'ALLOW' if allowed else 'DENY'}",
        "affected_by_reorg": False,
    }
