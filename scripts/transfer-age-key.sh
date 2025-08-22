#!/bin/bash
# Secure age key transfer helper

echo "🔐 Age Key Transfer Assistant"
echo "============================="
echo
echo "Choose transfer method:"
echo "1) USB drive transfer (most secure)"
echo "2) SSH transfer (if you have SSH access)"
echo "3) Encrypted file via GitHub (temporary)"
echo "4) QR code transfer (for small keys)"
echo "5) Manual encrypted email"
echo
read -p "Select option (1-5): " choice

AGE_KEY_PATH="${HOME}/.config/age/keys.txt"

case $choice in
    1)
        echo -e "\n📱 USB Drive Transfer"
        echo "====================="
        echo
        echo "On THIS machine (source):"
        echo "1. Insert USB drive"
        echo "2. Find mount point: lsblk or df -h"
        echo "3. Copy key to USB:"
        echo "   cp ~/.config/age/keys.txt /media/usb/age-key-backup.txt"
        echo
        echo "On NEW machine (destination):"
        echo "1. Insert USB drive"
        echo "2. Copy key from USB:"
        echo "   mkdir -p ~/.config/age"
        echo "   cp /media/usb/age-key-backup.txt ~/.config/age/keys.txt"
        echo "   chmod 600 ~/.config/age/keys.txt"
        echo "3. DELETE from USB:"
        echo "   shred -vfz /media/usb/age-key-backup.txt"
        ;;

    2)
        echo -e "\n🔌 SSH Transfer"
        echo "==============="
        echo
        echo "If you have SSH access between machines:"
        echo
        read -p "Enter destination hostname/IP: " dest_host
        read -p "Enter destination username: " dest_user

        echo
        echo "Run this command:"
        echo "scp ~/.config/age/keys.txt ${dest_user}@${dest_host}:~/age-key-temp.txt"
        echo
        echo "Then on destination machine:"
        echo "mkdir -p ~/.config/age"
        echo "mv ~/age-key-temp.txt ~/.config/age/keys.txt"
        echo "chmod 600 ~/.config/age/keys.txt"
        ;;

    3)
        echo -e "\n📦 GitHub Transfer (Temporary)"
        echo "==============================="
        echo
        echo "⚠️  This will temporarily store encrypted key in your repo"
        echo
        read -sp "Enter a passphrase for encryption: " passphrase
        echo
        read -sp "Confirm passphrase: " passphrase2
        echo

        if [ "$passphrase" != "$passphrase2" ]; then
            echo "❌ Passphrases don't match"
            exit 1
        fi

        echo
        echo "Encrypting age key..."
        # Use openssl for universal availability
        openssl enc -aes-256-cbc -salt -pbkdf2 -in ~/.config/age/keys.txt \
            -out age-key-transfer.enc -pass pass:"$passphrase"

        echo "✅ Created age-key-transfer.enc"
        echo
        echo "1. Commit this file:"
        echo "   git add age-key-transfer.enc"
        echo "   git commit -m 'Temporary: encrypted age key for transfer'"
        echo "   git push"
        echo
        echo "2. On new machine, pull and decrypt:"
        echo "   git pull"
        echo "   openssl enc -aes-256-cbc -d -pbkdf2 -in age-key-transfer.enc \\"
        echo "     -out ~/.config/age/keys.txt -pass pass:'your-passphrase'"
        echo "   chmod 600 ~/.config/age/keys.txt"
        echo
        echo "3. DELETE the encrypted file from repo:"
        echo "   git rm age-key-transfer.enc"
        echo "   git commit -m 'Remove temporary key transfer file'"
        echo "   git push"
        ;;

    4)
        echo -e "\n📱 QR Code Transfer"
        echo "==================="
        echo
        if ! command -v qrencode &> /dev/null; then
            echo "Installing qrencode..."
            sudo dnf install -y qrencode || sudo apt-get install -y qrencode
        fi

        echo "Generating QR code..."
        qrencode -t ANSIUTF8 < ~/.config/age/keys.txt

        echo
        echo "On new machine:"
        echo "1. Install QR scanner: sudo dnf install zbar"
        echo "2. Scan with webcam: zbarcam --raw"
        echo "3. Or type manually from QR display"
        echo "4. Save to ~/.config/age/keys.txt"
        echo "5. chmod 600 ~/.config/age/keys.txt"
        ;;

    5)
        echo -e "\n📧 Email Transfer"
        echo "================="
        echo
        echo "Encrypt the key for email:"
        echo
        read -sp "Enter a strong passphrase: " passphrase
        echo

        # Create encrypted version
        openssl enc -aes-256-cbc -salt -pbkdf2 -in ~/.config/age/keys.txt \
            -out ~/age-key-email.enc -pass pass:"$passphrase" -base64

        echo "✅ Created ~/age-key-email.enc (base64 encoded)"
        echo
        echo "1. Email the contents of ~/age-key-email.enc to yourself"
        echo "2. Share the passphrase via different channel (SMS, Signal, etc)"
        echo
        echo "On new machine, save email content to file and run:"
        echo "openssl enc -aes-256-cbc -d -pbkdf2 -in age-key-email.enc \\"
        echo "  -out ~/.config/age/keys.txt -pass pass:'passphrase' -base64"
        echo "chmod 600 ~/.config/age/keys.txt"
        ;;
esac

echo
echo "📝 Additional Notes:"
echo "- Age keys are in ~/.config/age/keys.txt"
echo "- Keep permissions at 600 (owner read/write only)"
echo "- Delete any temporary transfer files after success"
echo "- Consider rotating keys periodically"
