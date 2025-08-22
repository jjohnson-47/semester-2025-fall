#!/bin/bash
# Sync secrets between machines

echo "🔄 Syncing secrets configuration..."

# If using gopass
if command -v gopass &> /dev/null && [ -d ~/.local/share/gopass/stores/root/.git ]; then
    echo "Syncing gopass store..."
    cd ~/.local/share/gopass/stores/root
    git pull
    git push
    cd - > /dev/null
    echo "✅ Gopass synced"
fi

# If using encrypted file
if [ -f .env.secrets ] && command -v age &> /dev/null; then
    echo "Encrypting secrets for sync..."
    age -e -i ~/.config/age/keys.txt -o .env.secrets.age .env.secrets
    echo "✅ Encrypted .env.secrets.age ready for commit"
fi