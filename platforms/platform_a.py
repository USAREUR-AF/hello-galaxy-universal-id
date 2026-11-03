"""Platform A — Zenoh data-fabric consumer (the goat stack).

Spine-bound. It cares about exactly one thing: which write-namespace this peer
owns. That is the UUID, full stop. Because the UUID is in the persistent spine,
a reorg is INVISIBLE to Platform A — which is correct: task-organization is not
an identity change, and the fabric's access model must not churn when units are
re-assigned.

Stand-in note: the namespace string + reasoning are real (this is exactly the
ADR 1025 slot model); a live run would open an mTLS Zenoh session and publish
under it.
"""
from lib import descriptor


def write_namespace(desc):
    return f"{descriptor.uuid(desc)}/**"


def decision(desc, as_of=None):
    ns = write_namespace(desc)
    return {
        "platform": "A (Zenoh fabric)",
        "binds_to": "spine.uuid",
        "result": f"write-namespace {ns}",
        "affected_by_reorg": False,
    }
