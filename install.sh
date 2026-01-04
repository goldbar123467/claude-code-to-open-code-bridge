#!/bin/bash
#
# Agent Bridge Installer
# Usage: curl -sL https://raw.githubusercontent.com/goldbar123467/claude-code-to-open-code-bridge/main/install.sh | bash
#

set -e

INSTALL_DIR="$HOME/.agent-bridge"
REPO="https://github.com/goldbar123467/claude-code-to-open-code-bridge.git"

echo "🌉 Installing Agent Bridge..."

# Clone or update
if [ -d "$INSTALL_DIR" ]; then
    echo "   Updating existing installation..."
    cd "$INSTALL_DIR" && git pull -q
else
    echo "   Cloning repository..."
    git clone -q "$REPO" "$INSTALL_DIR"
fi

# Verify Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Test it works
cd "$INSTALL_DIR"
python3 -c "import bridge; print('   ✓ Bridge module OK')"

echo ""
echo "✅ Agent Bridge installed to $INSTALL_DIR"
echo ""
echo "📝 Add to your config:"
echo ""
echo "   Claude Code (~/.claude.json):"
echo '   { "mcpServers": { "bridge": { "command": "python3", "args": ["'$INSTALL_DIR'/mcp_server.py"] } } }'
echo ""
echo "   OpenCode (~/.config/opencode/config.json):"
echo '   { "mcp": { "bridge": { "command": "python3", "args": ["'$INSTALL_DIR'/mcp_server.py"] } } }'
echo ""
echo "🚀 Ready! Restart Claude Code or OpenCode to use the bridge."
