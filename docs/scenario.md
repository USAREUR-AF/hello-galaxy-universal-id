# Scenario — one identity, three platforms, one reorg

## Cast

A coalition task force. One entity we follow: **`RAVEN-03`**, an autonomous
sensor platform. Its identity descriptor is in `examples/raven-03.descriptor.json`.

Three platforms that share **no database, no runtime, and no vendor** — only the
descriptor standard and the peers' certs:

| Platform | Stand-in for | Authorizes off | What it cares about |
|---|---|---|---|
| **A** — Zenoh data-fabric consumer | the goat stack | UUID **spine** | which write-namespace RAVEN-03 owns |
| **B** — cert/SPIFFE-gated analytics service | an invented analytics vendor, "Acme Analytics" | cert CN + `role`/`echelon` | may this principal query dataset D? |
| **C** — external partner C2 | an invented autonomy vendor, "Northwind Autonomy" | the **affiliation graph** | is RAVEN-03 releasable to me right now? |

Each platform resolves the *same* descriptor and makes its *own* decision. None
of them coordinate. That is the point: a generalized identity standard means
consistency without coupling.

## The two halves of RAVEN-03's identity

**Persistent spine** (immutable, cert-anchored — "born-as"):
- `uuid` — the slot anchor; cert CN; Zenoh write-namespace; audit dedup key.
- `goatnet` / `urn` — which fabric, the URI-SAN scheme.
- `cert_fingerprint` — semi-persistent (rotates on renewal; the anchor it
  certifies never changes).

**Dynamic attributes** (registry-resolved, effective-dated — "currently-is"):
- `affiliation` + `parent` edge — who RAVEN-03 is task-organized under.
- `role`, `echelon`, `site` — its current posture.

## The event

At time **T = 2026-06-12T12:00Z**, RAVEN-03 is re-task-organized: its `parent`
edge moves from **org `falcon-bde`** to **org `condor-bde`**. This is a **single
registry edit** — `parent` edge `falcon-bde` gets `to_date = T`, a new `parent`
edge `condor-bde` opens at `from = T`. **No certificate is touched.** (In
`bin/demo` this is `lib/registry.retask`; the demo pins reference times so the
"current" view sits after T and the story is the same on every run.)

## What each platform does — before and after T

### Platform A (spine-bound) — *no change*
Resolves the spine. RAVEN-03's `uuid` is unchanged, so its write-namespace
`<uuid>/**` is unchanged. The reorg is invisible to the fabric's access model,
correctly — task-organization is not an identity change.

### Platform B (role-bound) — *no change*
Resolves `role`/`echelon` from the descriptor. The reorg didn't change RAVEN-03's
role, so its dataset-query authorization is unchanged. Correct.

### Platform C (graph-bound) — *flips coherently*
Platform C is operated by a partner who shares with `condor-bde` but **not**
`falcon-bde`.
- **Before T:** Platform C walks RAVEN-03's affiliation graph → parent is
  `falcon-bde` → not a shared partner → **RAVEN-03's data is not releasable to C.**
- **After T:** same walk → parent is now `condor-bde` → shared partner →
  **releasable.**

One registry edit; three platforms; each updates *coherently and independently*,
and the entity's cryptographic identity never moved.

## The traceability payoff (as-of-date)

An audit event `E` was logged at `2026-06-05T09:00Z` (before T) attributing data
to RAVEN-03. A reviewer later asks: *"who did RAVEN-03 report to when E happened?"*

Because edges are effective-dated, the answer is a graph walk **as-of E's
timestamp**, not "now": the `falcon-bde` edge was valid `[…, T)`, so the
as-of-`E` parent is **`falcon-bde`** — even though RAVEN-03's *current* parent is
`condor-bde`. The same document serves both the live COP and the forensic record.

## What this proves about the standard

1. **Persistent spine + dynamic attributes is the right cut.** Identity survives
   reorg; relationships move without re-keying.
2. **Born-as vs currently-is** resolves the cert/registry disagreement cleanly:
   each platform reads the half it needs.
3. **Effective-dated edges** give traceability for free — current and historical
   from one graph.
4. **Universal enforcement without coupling:** heterogeneous platforms enforce
   consistently off one portable document.

## Open scenario questions (track them here)

- ~~Does Platform C need anything beyond the descriptor + cert to make its
  releasability call offline?~~ **Demonstrated:** in `bin/demo`, Platform C
  decides from the descriptor + a local share policy alone — no fabric, no
  database. The "self-contained packet" claim holds for this case.
- Should the as-of-date walk be a descriptor capability or a registry query?
  (`lib/descriptor.resolve_parent` currently does it client-side over the edge
  set carried in the descriptor.)
- Minimal viable descriptor for an *external* consumer that never touches our
  fabric — which fields are truly required? (Platform C uses only `spine` +
  `attributes.edges`.)
