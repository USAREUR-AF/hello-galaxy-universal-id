"""Platform C — external partner C2 (stand-in for an invented
third-party vendor, "Northwind Autonomy").

Graph-bound, and the one that flips. Platform C holds ONLY the descriptor and
the peer's cert — no access to our fabric or database. It decides releasability
by walking the affiliation graph: "is this entity currently task-organized under
an org I share with?" When RAVEN-03 is re-task-organized from falcon-bde (not a
shared partner) to condor-bde (a shared partner), Platform C's answer flips from
DENY to ALLOW — coherently, off the same standard, with no coordination.

And because the edges are effective-dated, Platform C can answer the releasability
question AS-OF a past time too — the traceability payoff.

This also tests an open question from the design: a purely external consumer
makes its call offline from descriptor + a local share policy. Stdlib only.
"""
from lib import descriptor

# orgs this partner has a sharing arrangement with
SHARE_PARTNERS = {"urn:goat:zagros:org=condor-bde"}


def releasable(desc, as_of=None):
    parent = descriptor.resolve_parent(desc, as_of=as_of)
    ok = parent in SHARE_PARTNERS
    when = "now" if as_of is None else as_of.isoformat()
    return {
        "platform": "C (partner C2)",
        "binds_to": "affiliation graph",
        "result": (f"releasable ({when}): {'YES' if ok else 'no'} "
                   f"(parent={parent.split('org=')[-1] if parent else None})"),
        "affected_by_reorg": True,
    }


def grant(desc, registry, as_of=None):
    """v1.1: a GRANT decision is the 'new enemy'-sensitive case. It MUST be made
    against fresh data — a cached descriptor whose consistency token no longer
    matches the registry is rejected (fail-closed) and re-resolved live, rather
    than wrongly granting off a stale snapshot. This is the zookie discipline.

    `as_of` is the decision time. Returns (decision, detail).
    """
    if descriptor.is_fresh(desc, registry):
        parent = descriptor.resolve_parent(desc, as_of=as_of)
        ok = parent in SHARE_PARTNERS
        return ("GRANT" if ok else "deny",
                f"snapshot {descriptor.snapshot_token(desc)} is current; "
                f"parent={parent.split('org=')[-1] if parent else None}")
    # stale: do NOT grant off the cached graph — fetch fresh, then decide
    fresh = registry.resolve_live()
    parent = descriptor.resolve_parent(fresh, as_of=as_of)
    ok = parent in SHARE_PARTNERS
    return ("GRANT" if ok else "deny",
            f"cached {descriptor.snapshot_token(desc)} STALE "
            f"(registry at {registry.current_token()}) -> refused, re-resolved live; "
            f"parent now {parent.split('org=')[-1] if parent else None}")


def grant_naive(desc, as_of=None):
    """The ANTI-pattern, shown for contrast: grant straight off the cached
    descriptor with no freshness check. This is how a stale snapshot wrongly
    grants — Zanzibar's 'new enemy'."""
    parent = descriptor.resolve_parent(desc, as_of=as_of)
    ok = parent in SHARE_PARTNERS
    return ("GRANT" if ok else "deny",
            f"(no freshness check) cached {descriptor.snapshot_token(desc)}; "
            f"parent={parent.split('org=')[-1] if parent else None}")
