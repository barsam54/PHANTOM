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
sudo -n true || { echo "FAIL passwordless sudo required for verification"; exit 1; }
[[ "$PHANTOM_HOST_USER" != "$PHANTOM_WORKER_USER" ]] || { echo 'FAIL same UID'; exit 1; }
[[ "$(id -u "$PHANTOM_HOST_USER")" != "$(id -u "$PHANTOM_WORKER_USER")" ]] || { echo 'FAIL same UID'; exit 1; }
[[ "$(id -u "$PHANTOM_HOST_USER")" != 0 ]] || { echo 'FAIL root host'; exit 1; }
[[ "$PHANTOM_SOCKET_PATH" = /* && "$PHANTOM_MEMORY_DIR" = /* && "$PHANTOM_KEY_PATH" = /* ]] || exit 1
[[ "$(stat -c %u "$PHANTOM_KEY_PATH")" = "$(id -u "$PHANTOM_HOST_USER")" ]] || { echo 'FAIL key owner'; exit 1; }
[[ "$(stat -c %a "$PHANTOM_KEY_PATH")" = 600 || "$(stat -c %a "$PHANTOM_KEY_PATH")" = 400 ]] || { echo 'FAIL key mode'; exit 1; }
[[ "$(stat -c %u "$PHANTOM_MEMORY_DIR")" = "$(id -u "$PHANTOM_HOST_USER")" ]] || { echo 'FAIL memory owner'; exit 1; }
[[ "$(stat -c %a "$PHANTOM_MEMORY_DIR")" = 700 ]] || { echo 'FAIL memory mode'; exit 1; }
[[ "$(stat -c %a "$(dirname "$PHANTOM_SOCKET_PATH")")" = 710 ]] || { echo 'FAIL socket directory mode'; exit 1; }
[[ "$(stat -c %a "$PHANTOM_SOCKET_PATH")" = 660 ]] || { echo 'FAIL socket mode'; exit 1; }
[[ "$(stat -c %u "$PHANTOM_SOCKET_PATH")" = "$(id -u "$PHANTOM_HOST_USER")" ]] || { echo 'FAIL socket owner'; exit 1; }
socket_gid="$(stat -c %g "$PHANTOM_SOCKET_PATH")"
[[ " $(id -G "$PHANTOM_WORKER_USER") " == *" $socket_gid "* ]] || { echo 'FAIL worker not member of socket group'; exit 1; }
[[ "$(stat -c %g "$(dirname "$PHANTOM_SOCKET_PATH")")" = "$socket_gid" ]] || { echo 'FAIL socket directory group mismatch'; exit 1; }
[[ "$(stat -c %u "$(dirname "$PHANTOM_SOCKET_PATH")")" = "$(id -u "$PHANTOM_HOST_USER")" ]] || { echo 'FAIL socket directory owner'; exit 1; }
[[ ! -L "$PHANTOM_KEY_PATH" && ! -L "$PHANTOM_MEMORY_DIR" && ! -L "$PHANTOM_SOCKET_PATH" ]] || { echo 'FAIL symlink in protected paths'; exit 1; }
if [[ -n "${PHANTOM_OUTSIDER_USER:-}" ]]; then
    [[ "$(id -u "$PHANTOM_OUTSIDER_USER")" != "$(id -u "$PHANTOM_WORKER_USER")" ]] || { echo 'FAIL outsider shares worker UID'; exit 1; }
    [[ "$(id -u "$PHANTOM_OUTSIDER_USER")" != "$(id -u "$PHANTOM_HOST_USER")" ]] || { echo 'FAIL outsider shares host UID'; exit 1; }
    if sudo -n -u "$PHANTOM_OUTSIDER_USER" python3 - "$PHANTOM_SOCKET_PATH" <<'PY'
import socket, sys
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
    try:
        s.connect(sys.argv[1])
    except PermissionError:
        sys.exit(0)
    except OSError:
        sys.exit(1)
sys.exit(1)
PY
    then echo 'PASS outsider socket connection denied'; else echo 'FAIL outsider socket connection allowed or inconclusive'; exit 1; fi
fi
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
assert request(experiment).get("grant"), "authorized grant missing"
read_response = None
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
    client.settimeout(5)
    client.connect(path)
    client.sendall((json.dumps({"operation": "read", "experimentId": experiment, "cutoffUtc": cutoff}) + "\n").encode())
    response = b""
    while not response.endswith(b"\n") and len(response) < 65536:
        chunk = client.recv(8192)
        if not chunk: break
        response += chunk
    read_response = json.loads(response)
assert "record" in read_response, "authorized record read failed (seed admitted record before verification)"
assert read_response["record"].get("ExperimentId", read_response["record"].get("experimentId")) == experiment, "record scope mismatch"
print("PASS worker grant, trusted memory read and wrong-scope denial")
PY
echo 'PASS distinct UID, key custody, memory traversal denial and socket policy'
