#!/usr/bin/env bash
# Passive fingerprint of a public host for the reverse-engineering case: DNS chain, TLS
# issuer, full response headers along the redirect chain, and well-known files.
# Read-only — a handful of anonymous GETs to public URLs. Prints markdown for the casebook.
#
#   scripts/fingerprint.sh <host-or-url> [path]
#
# Interpretation of what the headers imply lives in ../REFERENCE.md, not here.
set -u

target="${1:?usage: fingerprint.sh <host-or-url> [path]}"
rest="${target#https://}"; rest="${rest#http://}"
host="${rest%%/*}"
urlpath="${rest#"$host"}"; urlpath="/${urlpath#/}"
path="${2:-$urlpath}"
ua="sherlock-fingerprint/1 (passive; curl)"
now=$(date -u +%Y-%m-%dT%H:%MZ)

echo "## Fingerprint: $host$path ($now)"
echo
echo "### DNS"
if command -v dig >/dev/null 2>&1; then
  for t in CNAME A AAAA; do dig +short "$host" "$t" | sed "s/^/- $t: /"; done
  apex=$(printf '%s' "$host" | awk -F. '{n=NF; if (n>=2) print $(n-1)"."$n; else print $0}')
  for t in NS MX TXT; do dig +short "$apex" "$t" | sed "s/^/- $t ($apex): /"; done
else
  getent hosts "$host" | sed 's/^/- A: /'
  echo "- (dig not installed: CNAME/NS/MX/TXT skipped)"
fi

echo
echo "### TLS"
curl -sSvI -A "$ua" --max-time 15 "https://$host/" 2>&1 \
  | grep -E '^\* +(subject|issuer|expire|start date|SSL connection|Certificate level)' | sed -E 's/^\* +/- /'

echo
echo "### Headers (GET https://$host$path, following redirects)"
curl -sS -o /dev/null -D - -L --max-redirs 5 -A "$ua" --max-time 20 -w '- final: %{url_effective} (%{num_redirects} redirects, %{time_total}s)\n' "https://$host$path" \
  | tr -d '\r' \
  | grep -viE '^(date|content-length|connection|transfer-encoding):' \
  | sed -E 's/^([Ss]et-[Cc]ookie: [^=]+)=[^;]*/\1=<redacted>/' \
  | sed -E 's/^HTTP\//\n- HTTP\//; s/^([a-zA-Z0-9-]+:)/- \1/' \
  | sed '/^$/d'

echo
echo "### Well-known"
for p in /robots.txt /sitemap.xml /.well-known/security.txt /.well-known/openid-configuration \
         /.well-known/apple-app-site-association /.well-known/assetlinks.json /humans.txt; do
  code=$(curl -sS -o /dev/null -w '%{http_code}' -L --max-redirs 3 -A "$ua" --max-time 10 "https://$host$p" 2>/dev/null || echo "err")
  echo "- $p → $code"
done

echo
echo "### robots.txt (first 25 lines)"
curl -sS -L --max-redirs 3 -A "$ua" --max-time 10 "https://$host/robots.txt" 2>/dev/null \
  | head -25 | sed 's/^/    /'
