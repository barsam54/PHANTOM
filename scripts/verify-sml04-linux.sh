#!/usr/bin/env bash
# Non-destructive SML-04 cross-UID deployment verification.
# Requires a running host, pre-provisioned distinct Linux accounts, and sudo -n.
set -euo pipefail
: "${PHANTOM_HOST_USER:?Set trusted host user}"
: "${PHANTOM_WORKER_USER:?Set worker user}"
: "${PHANTOM_SOCKET_PATH:?Set absolute socket path}"
: "${PHANTOM_MEMORY_DIR:?Set absolute private memory directory}"
: "${PHANTOM_KEY_PATH:?Set absolute private signing key path}"
: "${PHANTOM_EXPERIMENT_ID:?Set authorized experiment}"
: "${PHANTOM_CUTOFF_UTC:?Set ISO8601 UTC cutoff}"
[[ "$PHANTOM_HOST_USER" != "$PHANTOM_WORKER_USER" ]] || { echo 'FAIL same UID'; exit 1; }
[[ "$(id -u "$PHANTOM_HOST_USER")" != "$(id -u "$PHANTOM_WORKER_USER")" ]] || { echo 'FAIL same UID'; exit 1; }
[[ "$(id -u "$PHANTOM_HOST_USER")" != 0 ]] || { echo 'FAIL root host'; exit 1; }
[[ "$PHANTOM_SOCKET_PATH" = /* && "$PHANTOM_MEMORY_DIR" = /* && "$PHANTOM_KEY_PATH" = /* ]] || exit 1
sudo -n -u "$PHANTOM_HOST_USER" test -r "$PHANTOM_KEY_PATH"
sudo -n -u "$PHANTOM_HOST_USER" test -d "$PHANTOM_MEMORY_DIR"
if sudo -n -u "$PHANTOM_WORKER_USER" test -r "$PHANTOM_KEY_PATH"; then echo 'FAIL worker reads key'; exit 1; fi
if sudo -n -u "$PHANTOM_WORKER_USER" test -x "$PHANTOM_MEMORY_DIR"; then echo 'FAIL worker traverses memory'; exit 1; fi
sudo -n -u "$PHANTOM_WORKER_USER" python3 - "$PHANTOM_SOCKET_PATH" "$PHANTOM_EXPERIMENT_ID" "$PHANTOM_CUTOFF_UTC" <<'PY'
import json, socket, sys
path, experiment, cutoff = sys.argv[1:]
def request(experiment_id):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(5)
        client.connect(path)
        client.sendall((json.dumps({"experimentId": experiment_id, "cutoffUtc": cutoff}) + "\n").encode())
        response = b""
        while not response.endswith(b"\n") and len(response) < 8192:
            chunk = client.recv(8192 - len(response))
            if not chunk: break
            response += chunk
        return json.loads(response)
assert "grant" in request(experiment), "authorized worker denied"
assert request(experiment + "-unauthorized").get("error") == "denied", "scope bypass"
print("PASS worker socket authorization and wrong-scope denial")
PY
echo 'PASS distinct UID, key custody, memory traversal denial and socket policy'
