#!/usr/bin/env bash
# Register a recording.stopped webhook against a running Meetily instance,
# and save the one-time hmac_secret to a 0600 file for use with verify.sh.
#
# Usage:
#   MEETILY_PRO_TOKEN=<token> ./subscribe-and-verify.sh [receiver-url]
#
# Token: this script only needs Read, so the loopback token file works
# (turn on "Allow the CLI on this computer" in Settings > Integrations). A
# script that records, writes, or deletes needs a key you create: Settings >
# Integrations > Apps & scripts > Create key, tick the scope, copy the secret
# (shown once), turn on its Allow switch, export MEETILY_PRO_TOKEN.
#
# receiver-url defaults to http://127.0.0.1:9000/webhook. A loopback or
# private receiver must be added to "Local targets" under Settings >
# Integrations > Advanced BEFORE running this (takes effect immediately, no
# restart); otherwise registration fails with 400 bad_request.

set -euo pipefail

BASE="${MEETILY_BASE:-http://127.0.0.1:8420}"
WEBHOOK_URL="${1:-http://127.0.0.1:9000/webhook}"
SECRET_FILE="${SECRET_FILE:-./webhook-secret.txt}"

if [ -z "${MEETILY_PRO_TOKEN:-}" ]; then
  echo "Set MEETILY_PRO_TOKEN. This script only reads, so the loopback token works:" >&2
  echo "  export MEETILY_PRO_TOKEN=\"\$(cat ~/Library/Application\\ Support/pro.meetily.ai/gateway-token)\"   # macOS" >&2
  echo "For record/write/delete, create a key: Settings > Integrations > Apps & scripts > Create key." >&2
  exit 1
fi

echo "Registering webhook: recording.stopped -> $WEBHOOK_URL"

HTTP_RESPONSE=$(curl -sS -w '\n%{http_code}' -X POST "$BASE/v1/webhooks" \
  -H "Authorization: Bearer $MEETILY_PRO_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"$WEBHOOK_URL\", \"events\": [\"recording.stopped\"], \"delivery_mode\": \"at-least-once\"}")

HTTP_STATUS="${HTTP_RESPONSE##*$'\n'}"
RESPONSE="${HTTP_RESPONSE%$'\n'*}"

echo "$RESPONSE"

if [ "$HTTP_STATUS" -ge 400 ]; then
  # Real envelope: {"error":{"code","message","retryable"}}.
  ERROR_CODE=$(printf '%s' "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('error', {}).get('code', 'unknown'))" 2>/dev/null || echo "unknown")
  case "$ERROR_CODE" in
    unauthorized)
      echo "Error: unauthorized (401) -- the token is missing, unknown, expired, or revoked. Create a key in Settings > Integrations > Apps & scripts." >&2
      ;;
    consumer_disabled)
      echo "Error: consumer_disabled (403) -- this key's Allow switch is off (every key starts off). Turn it on in Settings > Integrations." >&2
      ;;
    insufficient_scope)
      echo "Error: insufficient_scope (403) -- this token lacks the scope for this call. Create a key with the scope you need: Settings > Integrations > Apps & scripts > Create key." >&2
      ;;
    bad_request)
      echo "Error: bad_request (400) -- if the message says 'url host is not allowed (loopback/private)', add this receiver's host:port under Settings > Integrations > Advanced > Local targets, then re-run." >&2
      ;;
    webhooks_disabled)
      echo "Error: webhooks_disabled (409) -- webhook delivery is off. Turn on 'Outgoing (webhooks)' under Settings > Integrations > Advanced." >&2
      ;;
    *)
      echo "Error: $ERROR_CODE (HTTP $HTTP_STATUS)" >&2
      ;;
  esac
  exit 1
fi

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
echo "  1. Keep $WEBHOOK_URL's host:port under Settings > Integrations > Advanced >"
echo "     Local targets while you use it (delivery re-checks it on every event)."
echo "  2. Check status: curl -H \"Authorization: Bearer \$MEETILY_PRO_TOKEN\" $BASE/v1/webhooks/$WEBHOOK_ID"
echo "     The first webhook a token registers to a host starts approval_state=pending and delivers nothing"
echo "     until you Allow it in the 'Waiting for you' strip at the top of Settings > Integrations"
echo "     (or later under Advanced > Destinations)."
echo "     Once allowed, POST $BASE/v1/webhooks/$WEBHOOK_ID/test fires a test delivery"
echo "     (409 host_not_approved before approval)."
echo "  3. Use verify.sh to check a received event's HMAC signature."
echo "  4. Clean up when done:"
echo "     curl -X DELETE -H \"Authorization: Bearer \$MEETILY_PRO_TOKEN\" $BASE/v1/webhooks/$WEBHOOK_ID"
