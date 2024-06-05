import json
import gc
import time
import machine
import network

# ANSI escape codes for colors
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_BLUE = "\033[94m"
COLOR_YELLOW = "\033[93m"

MAIN_DIR = "Star-Os"

gc.enable()

def load_wifi_credentials():
    """Loads Wi-Fi credentials from the saved JSON file."""
    try:
        with open(f"{MAIN_DIR}/wifi-credentials.json", "r") as f:
            wifi_credentials = json.load(f)
        return wifi_credentials['ssid'], wifi_credentials['password']
    except (OSError, ValueError, KeyError) as e:
        print(f"{COLOR_RED}Error loading Wi-Fi credentials: {e}{COLOR_RESET}")
        return None, None

def connect_to_wifi(ssid, password):
    """Connects to the Wi-Fi using the provided SSID and password."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    time.sleep(1)
    wlan.config(pm=wlan.PM_NONE)
    print(f"{COLOR_BLUE}Connecting to Wi-Fi...{COLOR_RESET}")
    wlan.connect(ssid, password)

    # Wait until connected
    max_wait = 10
    while max_wait > 0:
        if wlan.isconnected():
            break
        time.sleep(1)
        max_wait -= 1

    if wlan.isconnected():
        print(f"{COLOR_GREEN}Wi-Fi connected!{COLOR_RESET}")
        print(wlan.ifconfig())
        return True
    else:
        print(f"{COLOR_RED}Failed to connect to Wi-Fi, rebooting...{COLOR_RESET}")
        machine.reset()
        return False

def main_operations():
    """Main operations of the Star-OS system."""
    from microdot import Microdot
    print(f"{COLOR_BLUE}Star-OS started successfully!{COLOR_RESET}")

    # Initialize the web server
    app = Microdot()

    @app.route('/')
    def hello(request):
        return 'Hello, World! (running on micropython)'

    print(f"{COLOR_GREEN}Starting web server...{COLOR_RESET}")
    app.run(host='0.0.0.0', port=80)

def main():
    """Main function to load credentials, connect to Wi-Fi, and run operations."""
    ssid, password = load_wifi_credentials()
    if ssid and password:
        if connect_to_wifi(ssid, password):
            main_operations()
        else:
            print(f"{COLOR_RED}Unable to proceed without Wi-Fi connection.{COLOR_RESET}")
    else:
        print(f"{COLOR_RED}Wi-Fi credentials not found or invalid.{COLOR_RESET}")

if __name__ == "__main__":
    main()
