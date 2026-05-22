#!/bin/bash
# Phase 4 setup: Tailscale + nginx + launchd
# Run this script manually with: bash scripts/setup-phase4.sh

set -e

MICKEY_DIR="/Users/mickey/MICKEY"
CONFIG_DIR="$MICKEY_DIR/config"

echo "═══════════════════════════════════════════"
echo "  MICKEY Phase 4: Cross-Device Setup"
echo "═══════════════════════════════════════════"
echo ""

# ── Step 1: Tailscale ──
echo "▸ Step 1: Tailscale"
if ! command -v tailscale &>/dev/null; then
    echo "  Installing Tailscale via Mac App Store..."
    echo "  → Open: https://apps.apple.com/app/tailscale/id1475387142"
    echo "  → Or: brew install --cask tailscale"
    echo "  After installing, run: tailscale up"
    echo "  Then re-run this script."
    exit 1
fi

TS_STATUS=$(tailscale status --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Self',{}).get('DNSName','').rstrip('.'))" 2>/dev/null || echo "")
if [ -z "$TS_STATUS" ]; then
    echo "  Tailscale installed but not connected."
    echo "  Run: tailscale up"
    exit 1
fi

TS_HOSTNAME="$TS_STATUS"
echo "  ✓ Tailscale connected: $TS_HOSTNAME"

# ── Step 2: Tailscale HTTPS certs ──
echo ""
echo "▸ Step 2: HTTPS certificates"
tailscale cert --cert-file "$CONFIG_DIR/$TS_HOSTNAME.crt" --key-file "$CONFIG_DIR/$TS_HOSTNAME.key" "$TS_HOSTNAME" 2>/dev/null
echo "  ✓ Certs saved to $CONFIG_DIR/"

# ── Step 3: nginx ──
echo ""
echo "▸ Step 3: nginx"
if ! command -v nginx &>/dev/null; then
    echo "  Installing nginx..."
    brew install nginx
fi

# Generate nginx config with actual hostname
sed "s/TAILSCALE_HOSTNAME/$TS_HOSTNAME/g" "$CONFIG_DIR/nginx-mickey.conf" > /opt/homebrew/etc/nginx/servers/mickey.conf
echo "  ✓ nginx config installed"

# Test and reload
nginx -t 2>/dev/null && echo "  ✓ nginx config valid"
brew services restart nginx
echo "  ✓ nginx restarted"

# ── Step 4: launchd ──
echo ""
echo "▸ Step 4: Auto-start (launchd)"
PLIST_SRC="$CONFIG_DIR/com.mickey.assistant.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.mickey.assistant.plist"
cp "$PLIST_SRC" "$PLIST_DST"
launchctl unload "$PLIST_DST" 2>/dev/null || true
# Don't auto-load yet — user starts manually until ready
echo "  ✓ Plist installed at $PLIST_DST"
echo "  To enable auto-start: launchctl load $PLIST_DST"
echo "  To disable: launchctl unload $PLIST_DST"

# ── Done ──
echo ""
echo "═══════════════════════════════════════════"
echo "  ✓ Setup complete!"
echo ""
echo "  MICKEY is accessible at:"
echo "    Local:  http://localhost:5173"
echo "    Remote: https://$TS_HOSTNAME"
echo ""
echo "  Auth token (for remote access):"
cat "$MICKEY_DIR/data/auth_token" 2>/dev/null || echo "  (start MICKEY first to generate token)"
echo ""
echo "  Next: Install Tailscale on iPhone/iPad/Air"
echo "  iOS Shortcut: See scripts/ios-shortcut-guide.md"
echo "═══════════════════════════════════════════"
