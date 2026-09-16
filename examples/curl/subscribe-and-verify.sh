#!/usr/bin/env bash
# Register a recording.stopped webhook against a running Meetily instance,
# and save the one-time hmac_secret to a 0600 file for use with verify.sh.
#
# Usage:
#   MEETILY_PRO_TOKEN=<a read-scoped key> ./subscribe-and-verify.sh [receiver-url]
#
# receiver-url defaults to http://127.0.0.1:9000/webhook. If it is not
# loopback (or not already public), add its host:port to "Local webhook
# targets" in Settings > Pro > Integrations and RESTART Meetily first --
# the allowlist is only read at startup.

set -euo pipefail

BASE="${MEETILY_BASE:-http://127.0.0.1:8420}"
WEBHOOK_URL="${1:-http://127.0.0.1:9000/webhook}"
SECRET_FILE="${SECRET_FILE:-./webhook-secret.txt}"

if [ -z "${MEETILY_PRO_TOKEN:-}" ]; then
  echo "Set MEETILY_PRO_TOKEN to a key with the 'read' scope." >&2
  echo "Mint one in Settings > Pro > Integrations, or use the meetily-pro CLI." >&2
  exit 1
fi

echo "Registering webhook: recording.stopped -> $WEBHOOK_URL"

RESPONSE=$(curl -sS -X POST "$BASE/v1/webhooks" \
  -H "Authorization: Bearer $MEETILY_PRO_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"$WEBHOOK_URL\", \"events\": [\"recording.stopped\"], \"delivery_mode\": \"at-least-once\"}")

echo "$RESPONSE"

WEBHOOK_ID=$(printf '%s' "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
SECRET=$(printf '%s' "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['hmac_secret'])")

umask 077
printf '%s' "$SECRET" > "$SECRET_FILE"
chmod 600 "$SECRET_FILE"

echo
echo "Webhook id: $WEBHOOK_ID"
echo "hmac_secret saved to $SECRET_FILE (mode 600). It is returned only once by the API -- keep it."
echo
echo "Next steps:"
echo "  1. If $WEBHOOK_URL is not loopback or already public, add its host:port to"
echo "     'Local webhook targets' in Settings > Pro > Integrations, then RESTART Meetily"
echo "     (the allowlist is only read once at startup)."
echo "  2. Check status: curl -H \"Authorization: Bearer \$MEETILY_PRO_TOKEN\" $BASE/v1/webhooks/$WEBHOOK_ID"
echo "     A non-local destination starts as approval_state=pending and delivers nothing"
echo "     until you approve it under Destinations in the app."
echo "  3. Use verify.sh to check a received event's HMAC signature."
echo "  4. Clean up when done:"
echo "     curl -X DELETE -H \"Authorization: Bearer \$MEETILY_PRO_TOKEN\" $BASE/v1/webhooks/$WEBHOOK_ID"
