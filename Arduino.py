import serial
import time
import json
import requests

SERIAL_PORT = "COM3"  # Change as needed
BAUD_RATE = 9600
FLASK_API_URL = "http://127.0.0.1:5000/api/status"


try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Allow Arduino to initialize
    print(f"✅ Connected to Arduino on {SERIAL_PORT}")
except serial.SerialException:
    print(f"❌ Error: Unable to connect to {SERIAL_PORT}. Check connection.")
    arduino = None

def fetch_status():

    if not arduino:
        print("⚠️ Arduino not connected. Skipping data transmission.")
        return

    try:
        print("🔄 Fetching status from Flask API...")
        response = requests.get(FLASK_API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()

        print(f"📥 Received API Data: {data}")  
        status_dict = data.get("status", {})
        
        arduino_data = "".join("1" if status_dict.get(f"Load{i}") == "ON" else "0" for i in range(1, 6))
        print(f"📤 Sending to Arduino: {arduino_data}")

        arduino.write(arduino_data.encode())
        arduino.flush() 
        time.sleep(0.5)  
        
        print("✅ Data sent successfully.")

    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
    except serial.SerialException:
        print("❌ Serial communication error. Check Arduino connection.")

while True:
    fetch_status()
    time.sleep(2) 
