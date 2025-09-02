#!/usr/bin/env bash
set -e

# List users in /home
users=(/home/*)
echo "Available users:"
for i in "${!users[@]}"; do
    username=$(basename "${users[$i]}")
    echo "$((i+1)). $username"
done

# Ask the user to choose a user or another path
read -p "Enter the user number to install the application, or 0 for another path: " choice

if [ "$choice" -eq 0 ]; then
    read -p "Please enter the full path where you want to install the application: " install_path
else
    index=$((choice-1))
    install_path="${users[$index]}"
fi

# Check if the path exists
if [ ! -d "$install_path" ]; then
    echo "The path does not exist. Creating the directory..."
    mkdir -p "$install_path"
fi

echo "The application will be installed in: $install_path"


# Clone and install the project
apt install git curl python3-pip -y
git clone https://github.com/corazon008/AlcuinCalendar.git "$install_path/AlcuinCalendar"

curl -LsSf https://astral.sh/uv/install.sh | sh
cd "$install_path/AlcuinCalendar"
uv sync
chmod +x run.sh
chmod +x update.sh

# Create systemd service
sudo tee /etc/systemd/system/alcuin.service > /dev/null <<EOL
[Unit]
Description=Alcuin Calendar Service
After=network.target

[Service]
User=$CURRENT_USER
WorkingDirectory=$install_path/AlcuinCalendar
ExecStart=$install_path/AlcuinCalendar/run.sh
Restart=always
Environment=PYTHONUNBUFFERED=1
Environment=PATH=/usr/local/bin:/usr/bin:/bin:$install_path/.local/bin

[Install]
WantedBy=multi-user.target
EOL

# Enable the service
sudo systemctl daemon-reload
sudo systemctl enable alcuin
sudo systemctl start alcuin

echo "Installation complete. You can check the service status with: sudo systemctl status alcuin"
