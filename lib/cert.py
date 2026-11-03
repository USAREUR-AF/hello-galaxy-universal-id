"""The persistent-spine anchor: a REAL X.509 cert whose CN is the UUID.

This keeps the honesty matrix honest — the cert <-> UUID binding the demo relies
on is a genuine certificate, not a string compare on a made-up value. We shell
out to `openssl` (ubiquitous, no Python deps) to mint a throwaway self-signed
cert with CN = the slot anchor and a URI-SAN carrying the goat URN, then read
those fields back the same way any consumer would.
"""
import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CERT_DIR = os.path.join(REPO, ".cert")


def cert_path(uuid):
    return os.path.join(CERT_DIR, f"{uuid}.crt")


def key_path(uuid):
    return os.path.join(CERT_DIR, f"{uuid}.key")


def ensure_cert(uuid, urn):
    """Mint a self-signed leaf with CN=uuid and URI-SAN=urn if absent. Real openssl."""
    os.makedirs(CERT_DIR, exist_ok=True)
    crt, key = cert_path(uuid), key_path(uuid)
    if os.path.exists(crt):
        return crt
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
         "-keyout", key, "-out", crt, "-days", "30",
         "-subj", f"/CN={uuid}",
         "-addext", f"subjectAltName=URI:{urn}"],
        check=True, capture_output=True,
    )
    return crt


def _field(crt, *args):
    out = subprocess.run(["openssl", "x509", "-in", crt, "-noout", *args],
                         check=True, capture_output=True, text=True)
    return out.stdout.strip()


def cn_of(crt):
    # "subject=CN=<uuid>"  ->  <uuid>
    subj = _field(crt, "-subject")
    for part in subj.replace("subject=", "").split(","):
        part = part.strip()
        if part.upper().startswith("CN"):
            return part.split("=", 1)[1].strip()
    return None


def urisan_of(crt):
    ext = _field(crt, "-ext", "subjectAltName")
    for tok in ext.replace("\n", " ").split():
        tok = tok.strip().rstrip(",")
        if tok.startswith("URI:"):
            return tok[len("URI:"):]
    return None


def verify_binding(desc, crt):
    """The spine check every consumer does: the cert's CN must equal the
    descriptor's uuid, and the cert's URI-SAN must equal the descriptor's urn.
    Returns (ok, detail)."""
    want_uuid = desc["spine"]["uuid"]
    want_urn = desc["spine"]["urn"]
    got_cn = cn_of(crt)
    got_urn = urisan_of(crt)
    ok = (got_cn == want_uuid) and (got_urn == want_urn)
    detail = f"CN={got_cn}  URI-SAN={got_urn}"
    return ok, detail
