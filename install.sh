apt update && apt upgrade -y && \
sudo apt install python3-pip git curl -y && \
curl -LsSf https://astral.sh/uv/install.sh | sh && \
source $HOME/.local/bin/env && \
git clone https://github.com/corazon008/AlcuinCalendar.git && \
cd AlcuinCalendar && \
uv sync && \
chmod +x run.sh && \

echo "Creating systemd service..." && \
sudo tee /etc/systemd/system/alcuin.service > /dev/null <<EOL
[Unit]
Description=Alcuin Calendar Service
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/run.sh
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOL
echo "Systemd service created." && \
sudo systemctl daemon-reload && \
sudo systemctl enable alcuin && \
sudo systemctl start alcuin && \
echo "Installation complete. You can check the service status with: sudo systemctl status alcuin"
