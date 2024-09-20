# Coffee counter

A Python (Raspberry Pi) script that tracks the number of coffees brewed (Nespresso machine) by monitoring power usage data from a connected Shelly Plug via MQTT. It logs power data to a CSV file and uses a machine learning model to predict when coffee is being brewed based on power consumption patterns. The coffee count is saved and updated in a separate file, and notifications are sent upon each new brew.

## State of project

This project kind of works for my setup, but it’s not always spot on. The code is tailored to my specific situation and has not been optimized for easy installation or broader use. Documentation is minimal, so modifications may be required to fit your needs.

## Notes

`sudo nano /etc/mosquitto/conf.d/custom_port.conf`

Add 
```
listener 1883
allow_anonymous true
```
