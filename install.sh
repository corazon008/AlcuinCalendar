apt update && apt upgrade -y && \
curl -LsSf https://astral.sh/uv/install.sh | sh && \
sudo apt install python3-pip git -y && \
git clone https://github.com/corazon008/AlcuinCalendar.git && \
cd AlcuinCalendar && \
uv sync && \
chmod +x run.sh && \

sudo tee /etc/systemd/system/alcuin.service > /dev/null <<EOL
[Unit]
Description=Alcuin Calendar Service
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)/AlcuinCalendar
ExecStart=$(pwd)/AlcuinCalendar/run.sh
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOL && \

sudo systemctl daemon-reload && \
sudo systemctl enable alcuin && \
sudo systemctl start alcuin && \
echo "Installation complete. You can check the service status with: sudo systemctl status alcuin"
