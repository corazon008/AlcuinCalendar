#!/bin/bash
set -e

# Détection de l’utilisateur et du home
CURRENT_USER=$(whoami)
USER_HOME=$(eval echo ~$CURRENT_USER)

# Cloner et installer le projet
git clone https://github.com/corazon008/AlcuinCalendar.git "$USER_HOME/AlcuinCalendar"
cd "$USER_HOME/AlcuinCalendar"
chmod +x run.sh

# Création du service systemd
sudo tee /etc/systemd/system/alcuin.service > /dev/null <<EOL
[Unit]
Description=Alcuin Calendar Service
After=network.target

[Service]
User=$CURRENT_USER
WorkingDirectory=$USER_HOME/AlcuinCalendar
ExecStart=$USER_HOME/AlcuinCalendar/run.sh
Restart=always
Environment=PYTHONUNBUFFERED=1
Environment=PATH=/usr/local/bin:/usr/bin:/bin:$USER_HOME/.local/bin

[Install]
WantedBy=multi-user.target
EOL

# Activer le service
sudo systemctl daemon-reload
sudo systemctl enable alcuin
sudo systemctl start alcuin

echo "Installation complete. You can check the service status with: sudo systemctl status alcuin"
