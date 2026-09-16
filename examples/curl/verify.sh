#!/usr/bin/env bash
# Verify a Meetily webhook delivery's HMAC signature using only curl/openssl,
# no code -- useful for confirming what you're receiving on the wire.
#
# The signature is HMAC-SHA256, hex-encoded, over the string
# "{timestamp}.{body}", sent as the X-Meetily-Signature header in the form
# "sha256=<hex>". The timestamp comes from X-Meetily-Timestamp.
#
# Usage:
#   ./verify.sh <secret-file> <timestamp> <body-file> <signature-header-value>
#
# Example:
#   ./verify.sh ./webhook-secret.txt 1737033600 ./payload.json sha256=abc123...

set -euo pipefail

SECRET_FILE="${1:?usage: verify.sh <secret-file> <timestamp> <body-file> <signature>}"
TIMESTAMP="${2:?usage: verify.sh <secret-file> <timestamp> <body-file> <signature>}"
BODY_FILE="${3:?usage: verify.sh <secret-file> <timestamp> <body-file> <signature>}"
SIGNATURE="${4:?usage: verify.sh <secret-file> <timestamp> <body-file> <signature>}"

SECRET=$(cat "$SECRET_FILE")

HEX=$(
  { printf '%s.' "$TIMESTAMP"; cat "$BODY_FILE"; } \
    | openssl dgst -sha256 -hmac "$SECRET" \
    | sed 's/^.* //'
)
EXPECTED="sha256=$HEX"

if [ "$EXPECTED" = "$SIGNATURE" ]; then
  echo "OK: signature matches"
else
  echo "MISMATCH"
  echo "  expected: $EXPECTED"
  echo "  received: $SIGNATURE"
  exit 1
fi
