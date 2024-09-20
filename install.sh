#!/bin/bash

echo "Starting installation..."

echo "Updating package list and installing required system packages..."
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip mosquitto mosquitto-clients

if [ $? -ne 0 ]; then
    echo "Failed to install system packages. Exiting..."
    exit 1
fi

echo "System packages installed successfully."

if [ -d "coffee-counter" ]; then
    echo "Removing existing virtual environment..."
    rm -rf coffee-counter
fi

echo "Creating virtual environment (might take a while)..."
python3 -m venv coffee-counter

if [ $? -ne 0 ]; then
    echo "Failed to create virtual environment. Exiting..."
    exit 1
fi
echo "Virtual environment 'coffee-counter' created."

echo "Activating virtual environment..."
source coffee-counter/bin/activate

if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment. Exiting..."
    exit 1
fi

echo "Virtual environment activated."

echo "Upgrading pip and installing necessary Python libraries..."
pip install --upgrade pip

required_libraries=("numpy" "pandas" "scikit-learn" "joblib" "paho-mqtt" "scikit-learn" "asyncio" "websockets")

for lib in "${required_libraries[@]}"; do
    echo "Installing $lib..."
    pip3 install "$lib"
    if [ $? -ne 0 ]; then
        echo "Failed to install $lib. Exiting..."
        deactivate
        exit 1
    fi
done

echo "All Python libraries installed successfully."

CONFIG_FILE="/etc/mosquitto/conf.d/custom_port.conf"
echo "Configuring Mosquitto to use custom port and allow anonymous connections..."
if ! grep -q "listener 1883" "$CONFIG_FILE" || ! grep -q "allow_anonymous true" "$CONFIG_FILE"; then
    echo -e "listener 1883\nallow_anonymous true" | sudo tee "$CONFIG_FILE" > /dev/null
else
    echo "Mosquitto configuration already set."
fi

echo "Starting Mosquitto MQTT broker service..."
sudo systemctl enable mosquitto
sudo systemctl restart mosquitto

if [ $? -ne 0 ]; then
    echo "Failed to start Mosquitto service. Exiting..."
    deactivate
    exit 1
fi

echo "Mosquitto MQTT broker service started successfully."

echo "Creating systemd service for coffee-counter..."
SERVICE_FILE="/etc/systemd/system/coffee-counter.service"
if [ ! -f "$SERVICE_FILE" ]; then
    sudo bash -c "cat > $SERVICE_FILE" << EOL
[Unit]
Description=Coffee Counter Python Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/jan
ExecStart=/home/jan/coffee-counter/bin/python /home/jan/coffee_counter.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL
else
    echo "Service file already exists. Skipping creation."
fi

echo "Enabling and starting coffee-counter service..."
sudo systemctl daemon-reload
sudo systemctl enable coffee-counter.service
sudo systemctl restart coffee-counter.service

if [ $? -ne 0 ]; then
    echo "Failed to start coffee-counter service. Exiting..."
    deactivate
    exit 1
fi

echo "Coffee-counter service started successfully."

echo "Installation complete. The environment is ready for use."

deactivate
