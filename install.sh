apt update && apt upgrade -y && \
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
apt-get install -y ./google-chrome-stable_current_amd64.deb && \
sudo apt install python3-pip git -y && \
pip3 install webdriver-manager && \
mkdir AlcuinCalendarApp && cd AlcuinCalendarApp && \
git clone https://github.com/corazon008/AlcuinCalendar.git && \
pip3 install -r AlcuinCalendar/requirements.txt