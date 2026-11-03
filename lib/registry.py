"""The dynamic half: a tiny registry that holds the descriptor and applies a
re-task-organization as a pure registry edit.

The headline claim of the standard is that a reorg NEVER touches the cert — it
is an edit to the effective-dated edge set here. `retask` is that edit: close the
open parent edge at time T, open a new one. The spine (uuid, urn, cert binding)
is not touched.

v1.1 additions (from the cross-industry review): every snapshot carries a
freshness stamp (`resolved_at`) and an opaque consistency token
(`registry_snapshot`, a Zanzibar-zookie analog), and every edge carries a
transaction-time (`recorded_at`) alongside its valid-time window. The `Registry`
class models the live source of truth so a consumer can detect that a cached
descriptor is stale.

In goat this is the declared identity registry; here it is an
in-memory structure seeded from a candidate artifact. Stdlib only.
"""
import copy


# RAVEN-03's UUID spine — IMMUTABLE. The reorg below never changes any of this.
RAVEN03_UUID = "e7a9c75b532e3d434bb09fefd3ce1ec7"
RAVEN03_URN = "urn:goat:zagros:org=" + RAVEN03_UUID

FALCON = "urn:goat:zagros:org=falcon-bde"
CONDOR = "urn:goat:zagros:org=condor-bde"

REGISTRY_REF = "https://portal.example/api/identity/" + RAVEN03_UUID


def seed_before():
    """RAVEN-03 *before* the reorg: a single open parent edge under falcon-bde.
    Snapshot zk:1, stamped at the edge's record time."""
    return {
        "schema": "goat.identity.descriptor/v1",
        "spine": {
            "uuid": RAVEN03_UUID,
            "goatnet": "zagros",
            "urn": RAVEN03_URN,
            "slot_index": 14,
            "cert_fingerprint": "sha256:set-by-bin/setup",
        },
        "attributes": {
            "resolved_at": "2026-05-01T00:03:00Z",   # v1.1 freshness stamp
            "registry_snapshot": "zk:1",             # v1.1 consistency token (zookie analog)
            "registry_ref": REGISTRY_REF,            # v1.1 fetch-fresh pointer
            "alias": "raven-03",
            "display_name": "RAVEN-03 — autonomous sensor platform",
            "grammar": {
                "role": "OPERATOR",
                "affiliation": {"kind": "organic", "value": "raven-03"},
                "echelon": "COMPONENT",
                "node_class": "PLATFORM",
                "autonomy": "autonomous",
                "site": "zagros",
            },
            "edges": [
                {"rel": "parent", "to": FALCON,
                 "from": "2026-05-01T00:00:00Z", "to_date": None,
                 "recorded_at": "2026-05-01T00:03:00Z"},  # v1.1 transaction-time
            ],
        },
        "provenance": {
            "uuid": {"source": "cert", "authority": "born-as"},
            "urn": {"source": "cert", "authority": "born-as"},
            "affiliation": {"source": "registry", "authority": "currently-is"},
            "edges": {"source": "registry", "authority": "currently-is"},
            "role": {"source": "registry", "authority": "currently-is"},
        },
    }


def _next_token(tok):
    return "zk:" + str(int(tok.split(":")[1]) + 1)


def retask(desc, new_parent, at, recorded_at=None):
    """Re-task-organize: close the currently-open parent edge at time `at`, open a
    new parent edge under `new_parent` from `at`. Pure registry edit — the spine
    is untouched. Bumps the consistency token and freshness stamp. `at` /
    `recorded_at` are ISO-8601 strings (recorded_at defaults to `at`).

    Returns a new descriptor (does not mutate the input).
    """
    out = copy.deepcopy(desc)
    for e in out["attributes"]["edges"]:
        if e.get("rel") == "parent" and e.get("to_date") is None:
            e["to_date"] = at
    out["attributes"]["edges"].append(
        {"rel": "parent", "to": new_parent, "from": at, "to_date": None,
         "recorded_at": recorded_at or at}
    )
    out["attributes"]["registry_snapshot"] = _next_token(
        desc["attributes"].get("registry_snapshot", "zk:0"))
    out["attributes"]["resolved_at"] = recorded_at or at
    return out


class Registry:
    """The live source of truth. A consumer holding a cached descriptor can ask
    `current_token()` (a cheap liveness check) to learn its snapshot is stale, or
    `resolve_live()` to fetch fresh — the practical zookie/fetch-fresh contract."""

    def __init__(self, desc):
        self._state = copy.deepcopy(desc)

    def current_token(self):
        return self._state["attributes"]["registry_snapshot"]

    def resolve_live(self):
        """Return a fresh snapshot (what `registry_ref` would serve)."""
        return copy.deepcopy(self._state)

    def retask(self, new_parent, at, recorded_at=None):
        self._state = retask(self._state, new_parent, at, recorded_at)
        return self.current_token()
