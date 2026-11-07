# hello-galaxy: Universal identity

**One portable identity descriptor, consumed and enforced the same way across
platforms that share nothing else — shown, not told.**

This is the third repo in the **Hello Galaxy** series. Each Hello Galaxy is a
small, self-contained, runnable example of *best practice in one specific
dimension we work with* — the way "hello, world" is the smallest honest example
of a language. Series #1 covered Zenoh usage patterns; #2 covered moon-pod
standup + peering. **This one covers identity**: how a single, self-describing
identity *descriptor* lets heterogeneous platforms agree on *who* an entity is
and *what relationships it currently has* — without a shared database, a shared
runtime, or a shared vendor.

It follows the house style of the series: a short,
cold-readable runbook plus scripts that narrate what's happening, and an
**honesty matrix** that says plainly what is really enforced versus what is an
illustrative stand-in.

> **Status: runnable locally.** `python3 bin/demo` runs end to end with no
> third-party dependencies and a **real** openssl-minted cert for the spine
> binding. The descriptor schema is specified in goatcore's
> [identity-descriptor-standard](https://github.com/usareur-af/goatcore/blob/main/docs/design/identity-descriptor-standard.md);
> this repo builds consumers against the candidate artifact, so the sample
> descriptor and the stand-ins evolve with the standard. Platform A against a
> live Zenoh router is a planned addition; today it runs locally.

## Why this matters — what you can now do that you couldn't before

This isn't "a tidier identity file." Each row is something that was previously
impossible, or only possible with a bespoke per-pair integration, and becomes
routine once one portable, signed, freshness-stamped, graph-bearing identity
record exists:

| Before | Now, with one universal identity record |
|---|---|
| Every platform kept its own identity/attribute mapping; sharing an entity across two stacks meant a custom integration per pair. | Hand over **one record** — every platform enforces access + attribution off it. No shared database, no shared runtime, no shared vendor. |
| Re-organizing who a unit answers to risked re-issuing certs and touching every system. | A reorg is **one registry edit**. The identity never moves; every consumer updates coherently. |
| "Who did this report to *at the time of that event*?" needed log archaeology, if it was answerable at all. | A **time-travel query** answers current *and* historical — even what was *believed* at the moment of a past decision. |
| Identity decisions needed a live call to a central server — impossible off-network. | A **signed, freshness-stamped** record lets a disconnected edge node decide **offline**, with governed staleness bounds. |
| Coalition releasability was static lists or hand-marking. | "Is this entity under a partner I share with, right now / back then?" is a **graph query** off one record. |
| The same entity meant different things in each system, so cross-stack reasoning was manual. | One record **maps to each system** — recognizable across the whole stack and to an outside partner with none of our infrastructure. |
| A partner had to trust whatever we asserted over a call, or stand up a federation. | The record is **verifiable offline** — its origin/integrity check against a signature, its identity against the cert, with no callback to us. |

**In one line:** a single identity that *travels, stays current, proves itself,
and means the same thing everywhere* — including off-network and across vendors
who share nothing else. The demo below shows each of these against real code.

## Run it

```
python3 bin/demo      # the whole story; mints a throwaway cert on first run
python3 bin/setup     # (optional) pre-mint the cert; re-mint after rm -rf .cert
```

Needs Python 3 and `openssl` (the cert step self-reports as skipped if openssl
is absent; everything else still runs).

---

## The idea in one paragraph

An identity has two halves with different physics. A **persistent spine** —
born with the identity, immutable, cryptographically anchored in the peer's
certificate: its UUID, the fabric it belongs to, its cert binding. And a set of
**dynamic attributes** — its current affiliation, command relationship, role,
echelon, site — which legitimately *change over time* (units get re-task-organized;
people get promoted; systems relocate) and which therefore live in a registry,
not the cert. The descriptor carries both, tags every field with whether the
**certificate** ("born-as") or the **registry** ("currently-is") is authoritative,
and records relationships as **effective-dated edges** so the same document answers
both "who does this report to *now*?" and "who did it report to *on the date of
that audit event*?"

Give that one document to platforms that share nothing else, and they can each
enforce access and attribution **coherently** off it.

## The artifact — one reusable record

This is the whole point of the standard, made concrete. A single, portable,
self-describing record that any platform can read. Every consumer in this repo —
and any outside platform we share with — reuses *this same document*; none of it
is platform-specific.

```jsonc
// examples/raven-03.descriptor.json (annotated; the real file is plain JSON)
{
  "schema": "goat.identity.descriptor/v1",

  "spine": {                                    // immutable, cert-anchored — "born-as"
    "uuid": "e7a9c75b532e3d434bb09fefd3ce1ec7", //   never changes, never reused
    "goatnet": "zagros",
    "urn": "urn:goat:zagros:org=e7a9c75b…",
    "cert_fingerprint": "sha256:…"             //   rotates; the anchor it certifies does not
  },

  "attributes": {                               // registry-resolved — "currently-is"
    "alias": "raven-03",
    "grammar": { "role": "OPERATOR", "echelon": "COMPONENT",
                 "node_class": "PLATFORM", "site": "zagros" },
    "edges": [                                  // effective-dated relationship graph
      { "rel": "parent", "to": "urn:goat:zagros:org=falcon-bde",
        "from": "2026-05-01T00:00:00Z", "to_date": "2026-06-12T12:00:00Z" },  // closed at the reorg
      { "rel": "parent", "to": "urn:goat:zagros:org=condor-bde",
        "from": "2026-06-12T12:00:00Z", "to_date": null }                     // open = current
    ]
  },

  "provenance": {                               // per field: which source is authoritative
    "urn":         { "source": "cert",     "authority": "born-as" },
    "affiliation": { "source": "registry", "authority": "currently-is" }
  },

  "extensions": { "x-owner/...": "namespaced escape hatch; unknown keys ignored, never fatal" }
}
```

The "universal / reusable" claim is literal: **Platform A** reads only `spine`,
**Platform B** reads `grammar.role`, **Platform C** walks `edges` — the *same*
record, three unrelated consumers, no coordination and no shared backend. The
`provenance` block is what lets them disagree safely (cert = born-as, registry =
currently-is), and the `extensions` namespace is how a consumer carries its own
fields without forking the standard.

## The scenario (`docs/scenario.md`)

A coalition task force where three independent platforms must act on the same
identities — standing in for how a third-party analytics stack (here "Acme Analytics"), a
third-party autonomy stack ("Northwind Autonomy"), and the goat data fabric might each consume
**one generalized, universally-enforced identity standard**:

- **Platform A — Zenoh data-fabric consumer** (the goat stack). Enforces
  write-namespace + ACL off the UUID **spine**.
- **Platform B — cert/SPIFFE-gated analytics service** (invented vendor stand-in).
  Authorizes API calls off the cert CN + the descriptor's role/echelon.
- **Platform C — external partner C2** (invented vendor stand-in). Holds *only* the
  descriptor + the peer's cert; uses the **affiliation graph** to decide
  releasability ("is this unit under a coalition partner I share with?").

**The event:** a unit, `RAVEN-03`, is re-task-organized — its `parent`
affiliation edge moves from one org to another at time *T*. This is a **registry
edit, not a re-mint.**

**What the demo shows:**

1. RAVEN-03's UUID **spine never moves** → all three platforms still recognize
   the *same entity* across the reorg (zero identity churn, no re-keying).
2. Re-resolving the descriptor, each platform updates **coherently**: Platform
   C's releasability flips (now under the new partner); Platform A's namespace
   is unchanged (spine-bound); Platform B's role access is unchanged.
3. An **as-of-date** query — "who did RAVEN-03 report to at audit event *E*,
   before *T*?" — returns the *old* parent via the effective-dated edge. That's
   the traceability payoff.

## What a run looks like

`python3 bin/demo`, abridged — the same record (above) read by three platforms,
through one reorg:

```
[spine] persistent identity (immutable, cert-anchored)
  cert CN <-> UUID binding: VERIFIED  (CN=e7a9c75b…  URI-SAN=urn:goat:zagros:org=e7a9c75b…)
  uuid       : e7a9c75b532e3d434bb09fefd3ce1ec7   <- never changes, never reused

[before reorg]  current parent = falcon-bde
    A (Zenoh fabric)     [spine.uuid      ] write-namespace e7a9c75b…/**
    B (analytics svc)    [grammar.role    ] query 'sensor-feeds' as role OPERATOR: ALLOW
  ↻ C (partner C2)       [affiliation graph] releasable: no  (parent=falcon-bde)

[event] RAVEN-03 re-task-organized -> condor-bde   (a REGISTRY EDIT; the cert is not touched)

[after reorg]   current parent = condor-bde   (uuid unchanged — identity did not move)
    A (Zenoh fabric)     [spine.uuid      ] write-namespace e7a9c75b…/**          (unchanged)
    B (analytics svc)    [grammar.role    ] query 'sensor-feeds' as role OPERATOR: ALLOW  (unchanged)
  ↻ C (partner C2)       [affiliation graph] releasable: YES (parent=condor-bde)  (flipped)

[traceability]  'who did RAVEN-03 report to at an audit event before the reorg?' -> falcon-bde
                (the old parent, via the effective-dated walk — not the current one)
```

One record, reused: the identity never moved, only the relationship-bound
platform's decision changed, and the historical question still answers correctly.

The run ends with the **v1.1 freshness act**:

```
[v1.1 freshness]  the 'new enemy' staleness hazard, and the consistency-token fix
  consumer holds cached snapshot zk:2 (parent=condor, a shared partner)
  registry has since advanced to zk:3 (a 2nd reorg moved RAVEN-03 back to falcon-bde)
  NAIVE grant off the cache : GRANT  <- WRONG (new enemy)
  v1.1 grant (token-checked): deny   <- correct (cache STALE -> refused, re-resolved live; parent now falcon-bde)
```

## v1.1 — freshness, consistency, and bitemporal edges

A cross-industry review of identity/credential standards (SPIFFE, X.509 attribute
certs, W3C VC/DID, Google Zanzibar, NIST ABAC, bitemporal databases) validated
the architecture and surfaced one real hazard worth showing: **a portable
document that embeds a *mutable* graph is stale the instant a relationship
changes.** Zanzibar — the reference design for relationship-based access — avoids
this by *not* shipping a portable graph; it keeps tuples in a consistency-stamped
service and hands out opaque tokens (zookies) so a decision is bound to a
snapshot. The canonical "new enemy" bug is a grant decided against a snapshot
staler than the truth → a **wrongful grant**.

v1.1 closes it without abandoning the portable document:

- **Consistency token** — the descriptor carries `registry_snapshot` (a zookie
  analog) + `resolved_at` + a `registry_ref` fetch-fresh pointer. A *grant*
  decision must be made against a current token or re-resolved live; a
  *display/forensic* read may use the cache. `lib/descriptor.is_fresh()` +
  `platforms/platform_c.grant()` implement exactly this, and `grant_naive()`
  shows the wrongful-grant anti-pattern for contrast.
- **Bitemporal edges** — each edge now carries `recorded_at` (transaction-time:
  *when we learned it*) alongside its `from`/`to_date` valid-time window, so an
  audit can reconstruct what was *believed* at a past decision, not just what was
  eventually true.

This keeps the document portable (still works offline at the denied edge, which
NIST SP 800-162 explicitly blesses) while making high-consequence grants
freshness-disciplined.

## v1.2 — offline verifiability (document signing)

The cert proves the **spine**; it says nothing about the dynamic attributes. So a
partner who caches the record and reads it offline gets a **second trust root**:
a detached signature over the canonical document, made by the *registry* key
(`lib/docsig.py`, real openssl). The cert vouches for the identity, the registry
signature vouches for the relationships — both verifiable with **no callback to
us**. The run shows a valid verify and a tamper being rejected:

```
[v1.2 signing]  the registry signs the document; a partner verifies it offline
  registry-signed `sig` present; partner offline-verify: VALID
  tamper one edge target, re-verify with same sig: REJECTED  <- tamper caught
```

The standard also pins JSON as the canonical form with a CBOR/COSE profile for
constrained radio bearers, and a `?v=<major>` version-negotiation rule — see the
[design doc](https://github.com/usareur-af/goatcore/blob/main/docs/design/identity-descriptor-standard.md)
and [ADR 1051](https://github.com/usareur-af/goatcore/blob/main/docs/adr/1051-identity-descriptor-standard.md) Amendment 2.

## Honesty matrix

| Element | Real | Stand-in / simulated |
|---|---|---|
| Identity descriptor format | ✅ the candidate standard artifact | |
| Persistent-spine / dynamic-attribute split | ✅ as designed | |
| Effective-dated graph traversal (current + as-of-date) | ✅ real logic | |
| Cert CN ↔ UUID binding | ✅ real X.509 (openssl-minted, verified in `bin/demo`) | |
| The reorg as a registry edit (no cert churn) | ✅ real (`lib/registry.retask`) | |
| v1.1 consistency token / freshness gate on grants | ✅ real (`is_fresh` + `grant` vs `grant_naive`) | token is an in-demo counter; a real zookie is registry-issued |
| v1.1 bitemporal `recorded_at` edges | ✅ carried in the artifact + resolver | |
| v1.2 offline document signature + tamper rejection | ✅ real openssl (`lib/docsig.py`, registry key) | demo registry key is throwaway; prod key is registry-held |
| Platform A (Zenoh consumer) | ✅ namespace logic real, runs locally | a live mTLS Zenoh session is not part of this demo |
| Platform B / Platform C | ✅ run locally; the *consumption pattern* is real | Acme Analytics and Northwind Autonomy are invented names for integration patterns |
| Registry | ✅ runs locally (in-memory, seeded from the candidate artifact) | in goat the registry is the declared identity registry |

## Layout

```
README.md            this file
bin/demo             the narrated end-to-end demo
bin/setup            pre-mint the throwaway cert (optional)
lib/descriptor.py    load + resolve (current + as-of-date edge walk)
lib/registry.py      the dynamic half: seed + retask (the reorg, no cert churn)
lib/cert.py          real openssl cert minting + CN/URI-SAN <-> spine binding
lib/docsig.py        registry document signature (v1.2)
platforms/           three stand-ins: A (spine), B (role), C (affiliation graph)
docs/scenario.md     the full cross-platform scenario + sequence
examples/            candidate identity descriptor (the artifact under test)
LICENSE              Apache-2.0
```

## Where this comes from

The standard this repo demonstrates is specified in goatcore at
[`docs/design/identity-descriptor-standard.md`](https://github.com/usareur-af/goatcore/blob/main/docs/design/identity-descriptor-standard.md)
and decided in [ADR 1051](https://github.com/usareur-af/goatcore/blob/main/docs/adr/1051-identity-descriptor-standard.md).
This repo is the runnable proof that the standard is consumable across platforms.

## Licence

`hello-galaxy-universal-id` was written by U.S. Federal government employees. In the U.S. it is not subject to copyright and is in the public domain; in countries where copyright is recognized, it is released under the [Apache License 2.0](LICENSE). See [INTENT.md](INTENT.md). See also [NOTICE](NOTICE),
[CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
