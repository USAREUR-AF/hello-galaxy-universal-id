"""Identity descriptor: load + resolve.

The whole point of the standard: a persistent spine (immutable, cert-anchored)
plus dynamic, effective-dated relationship edges. This module is the resolver —
it answers "who is the parent now?" and "who was the parent as-of date X?" off
the *same* edge set. That dual answer is the traceability payoff.

Stdlib only.
"""
import json
from datetime import datetime, timezone


def _parse_ts(s):
    """ISO-8601 with trailing Z accepted on every Python 3."""
    if s is None:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def load(path):
    with open(path) as f:
        return json.load(f)


def uuid(desc):
    return desc["spine"]["uuid"]


def urn(desc):
    return desc["spine"]["urn"]


def role(desc):
    return desc["attributes"]["grammar"]["role"]


def parent_edges(desc):
    return [e for e in desc["attributes"].get("edges", []) if e.get("rel") == "parent"]


def resolve_parent(desc, as_of=None):
    """Return the parent URN effective at `as_of` (a datetime), or now if None.

    An edge is in effect when  from <= t < to_date  (to_date None = still open).
    This is the born-vs-now distinction made operational: change `as_of` and the
    same document yields the historical parent, with no separate history store.
    """
    t = as_of if as_of is not None else datetime.now(timezone.utc)
    for e in parent_edges(desc):
        start = _parse_ts(e.get("from"))
        end = _parse_ts(e.get("to_date"))
        if (start is None or start <= t) and (end is None or t < end):
            return e["to"]
    return None


def edge_tuples(desc):
    """(to, from, to_date) for each parent edge — used to compare/validate states."""
    return sorted(
        (e["to"], e.get("from"), e.get("to_date")) for e in parent_edges(desc)
    )


# --- v1.1: freshness / consistency (the Zanzibar-zookie analog) ---------------

def snapshot_token(desc):
    """The opaque consistency token this snapshot was resolved at (zookie analog)."""
    return desc["attributes"].get("registry_snapshot")


def resolved_at(desc):
    return desc["attributes"].get("resolved_at")


def is_fresh(desc, registry):
    """A cached descriptor is fresh iff its consistency token equals the registry's
    current token. This is the cheap liveness check that closes the 'new enemy'
    staleness hazard for grant decisions (cf. Zanzibar zookies)."""
    return snapshot_token(desc) == registry.current_token()
