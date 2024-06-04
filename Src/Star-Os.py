import json
import os
import time
import machine
import network
from microdot import Microdot

# ANSI escape codes for colors
color_reset = "\033[0m"
color_red = "\033[91m"
color_green = "\033[92m"
color_blue = "\033[94m"
color_yellow = "\033[93m"

MainDir = "Star-Os"

def load_wifi_credentials():
    """Loads Wi-Fi credentials from the saved JSON file."""
    try:
        with open(f"{MainDir}/wifi-credentials.json", "r") as f:
            wifi_credentials = json.load(f)
        return wifi_credentials['ssid'], wifi_credentials['password']
    except (OSError, ValueError, KeyError) as e:
        print(f"{color_red}Error loading Wi-Fi credentials: {e}{color_reset}")
        return None, None

def connect_to_wifi(ssid, password):
    """Connects to the Wi-Fi using the provided SSID and password."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    time.sleep(1)
    wlan.config(pm=wlan.PM_NONE)
    print(f"{color_blue}Connecting to Wi-Fi...{color_reset}")
    wlan.connect(ssid, password)

    # Wait until connected
    max_wait = 10
    while max_wait > 0:
        if wlan.isconnected():
            break
        time.sleep(1)
        max_wait -= 1

    if wlan.isconnected():
        print(f"{color_green}Wi-Fi connected!{color_reset}")
        print(wlan.ifconfig())
        return True
    else:
        print(f"{color_red}Failed to connect to Wi-Fi, rebooting...{color_reset}")
        machine.reset()
        return False

def main_operations():
    """Main operations of the Star-OS system."""
    print(f"{color_blue}Star-OS started succesfully!{color_reset}")

    # Initialize the web server
    app = Microdot()

    @app.route('/')
    def hello(request):
        return 'Hello, World!(running on micropython)'

    print(f"{color_green}Starting web server...{color_reset}")
    app.run(host='0.0.0.0', port=80)

def main():
    """Main function to load credentials, connect to Wi-Fi, and run operations."""
    ssid, password = load_wifi_credentials()
    if ssid and password:
        if connect_to_wifi(ssid, password):
            main_operations()
        else:
            print(f"{color_red}Unable to proceed without Wi-Fi connection.{color_reset}")
    else:
        print(f"{color_red}Wi-Fi credentials not found or invalid.{color_reset}")

if __name__ == "__main__":
    main()
