#!/bin/sh

cd /home/gabi/PycharmProjects/whatsapp

sudo apt install python3-pip -y

sudo apt install python3-venv -y

sudo apt-get install python3-dev -y

python3 -m venv venv

source venv/bin/activate

pip3 install wheel

pip3 install -r requirements.txt

echo "
#!/usr/bin/env bash
cd  /home/gabi/PycharmProjects/whatsapp
source venv/bin/activate
python3 whatsapp.py
" > whatsapp.sh

sudo chmod +x whatsapp.sh
sudo mv whatsapp.sh /bin/whatsapp

sudo touch /etc/systemd/system/whatsapp.service
sudo chmod 775 /etc/systemd/system/whatsapp.service
sudo chmod a+w /etc/systemd/system/whatsapp.service

sudo echo "
[Unit]
Description= whatsapp
[Service]
User=gabi
ExecStart=/bin/bash /bin/whatsapp
Restart=on-failure
WorkingDirectory=/home/gabi
StandardOutput=syslog
StandardError=syslog
[Install]
WantedBy=multi-user.target
" > /etc/systemd/system/whatsapp.service

sudo systemctl enable whatsapp.service
sudo systemctl daemon-reload