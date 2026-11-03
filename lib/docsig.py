"""Document signing — the second trust root (v1.2, ADR 1051 Amendment 2).

The cert vouches for the SPINE. It says nothing about the dynamic attributes, so
a partner who caches the descriptor and reads it offline has no way to prove the
attributes/edges actually came from the registry. This module adds the missing
root: a REAL detached signature over the canonical document, made by the
*registry* key (not the peer cert — the registry is authoritative for the dynamic
half). A consumer verifies it offline, with no call back to us.

We shell out to `openssl` (no Python deps), RSA + SHA-256 (portable across openssl
versions). Canonicalization is sort-keys/compact JSON over the document minus the
`sig` field itself (a stand-in for JCS).
"""
import base64
import json
import os
import subprocess
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CERT_DIR = os.path.join(REPO, ".cert")
REG_KEY = os.path.join(CERT_DIR, "registry.key")
REG_PUB = os.path.join(CERT_DIR, "registry.pub")


def ensure_registry_key():
    """Mint the registry's throwaway signing keypair if absent. Real openssl."""
    os.makedirs(CERT_DIR, exist_ok=True)
    if not os.path.exists(REG_KEY):
        subprocess.run(["openssl", "genpkey", "-algorithm", "RSA",
                        "-pkeyopt", "rsa_keygen_bits:2048", "-out", REG_KEY],
                       check=True, capture_output=True)
    if not os.path.exists(REG_PUB):
        subprocess.run(["openssl", "rsa", "-in", REG_KEY, "-pubout", "-out", REG_PUB],
                       check=True, capture_output=True)
    return REG_PUB


def canonical(desc):
    """Deterministic bytes to sign: the document minus its own `sig` field."""
    d = {k: v for k, v in desc.items() if k != "sig"}
    return json.dumps(d, sort_keys=True, separators=(",", ":")).encode()


def sign(desc):
    """Return a base64 detached registry signature over the canonical document."""
    ensure_registry_key()
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(canonical(desc))
        msg = f.name
    sig = msg + ".sig"
    try:
        subprocess.run(["openssl", "dgst", "-sha256", "-sign", REG_KEY, "-out", sig, msg],
                       check=True, capture_output=True)
        return base64.b64encode(open(sig, "rb").read()).decode()
    finally:
        for p in (msg, sig):
            if os.path.exists(p):
                os.remove(p)


def verify(desc, sig_b64):
    """Verify the detached registry signature over the document. Returns bool.
    This is what an offline consumer does before trusting the dynamic attributes."""
    ensure_registry_key()
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(canonical(desc))
        msg = f.name
    sig = msg + ".sig"
    try:
        open(sig, "wb").write(base64.b64decode(sig_b64))
        r = subprocess.run(["openssl", "dgst", "-sha256", "-verify", REG_PUB,
                            "-signature", sig, msg], capture_output=True)
        return r.returncode == 0
    finally:
        for p in (msg, sig):
            if os.path.exists(p):
                os.remove(p)
