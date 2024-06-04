import json
import machine
import os
import gc
import time

# ANSI escape codes for colors
color_reset = "\033[0m"
color_red = "\033[91m"
color_green = "\033[92m"
color_yellow = "\033[93m"
color_blue = "\033[94m"
color_cyan = "\033[96m"

# Main directory for storing Wi-Fi credentials
MainDir = "Star-Os"

def detect_board():
    board_info = {}

    try:
        # Getting frequency in MHz for easier reading
        freq = machine.freq()
        if isinstance(freq, tuple):  # If freq returns a tuple (ESP32, for example)
            board_info['freq'] = ' / '.join(f'{f // 10**6} MHz' for f in freq)
        else:
            board_info['freq'] = f'{freq // 10**6} MHz'
    except Exception as e:
        board_info['freq'] = "Unknown"
        print(f"{color_red}Error retrieving frequency: {e}{color_reset}")

    try:
        # Getting the board name and firmware details
        uname = os.uname()
        board_info['board'] = uname.machine
        board_info['version'] = uname.version
        board_info['release'] = uname.release
    except AttributeError:
        board_info['board'] = "Unknown"
        board_info['version'] = "Unknown"
        board_info['release'] = "Unknown"
        print(f"{color_red}Error retrieving uname information{color_reset}")

    try:
        # Getting memory information
        board_info['mem_free'] = gc.mem_free()
        board_info['mem_alloc'] = gc.mem_alloc()
    except Exception as e:
        board_info['mem_free'] = "Unknown"
        board_info['mem_alloc'] = "Unknown"
        print(f"{color_red}Error retrieving memory information: {e}{color_reset}")

    # Check Wi-Fi support
    try:
        import network
        board_info['wifi_support'] = 'yes' if 'WLAN' in dir(network) else 'no'
    except ImportError:
        board_info['wifi_support'] = 'no'

    return board_info

def save_setup_info(board_info):
    try:
        with open("setupinfo.json", "w") as f:
            json.dump(board_info, f)
    except Exception as e:
        print(f"{color_red}Error saving setup info: {e}{color_reset}")

def save_wifi_credentials(ssid, password):
    wifi_credentials = {
        'ssid': ssid,
        'password': password
    }
    try:
        # Check if directory exists and create if not
        if MainDir not in os.listdir():
            os.mkdir(MainDir)
        with open(f"{MainDir}/wifi-credentials.json", "w") as f:
            json.dump(wifi_credentials, f)
    except Exception as e:
        print(f"{color_red}Error saving Wi-Fi credentials: {e}{color_reset}")

def load_wifi_credentials():
    try:
        with open(f"{MainDir}/wifi-credentials.json", "r") as f:
            wifi_credentials = json.load(f)
        return wifi_credentials['ssid'], wifi_credentials['password']
    except (OSError, ValueError, KeyError) as e:
        return None, None

def print_colored_info(info):
    try:
        with open("setupinfo.json", "r") as f:
            json_data = json.load(f)

        print(f"{color_cyan}Board Information:{color_reset}")
        print(f"{color_green}Board: {color_reset}{json_data['board']}")
        print(f"{color_green}Micropython Version: {color_reset}{json_data['version']}")
        print(f"{color_green}Micropython Release: {color_reset}{json_data['release']}")
        print(f"{color_green}CPU Frequency: {color_reset}{json_data['freq']}")
        print(f"{color_green}Free Memory: {color_reset}{json_data['mem_free']} bytes")
        print(f"{color_green}Allocated Memory: {color_reset}{json_data['mem_alloc']} bytes")
        print(f"{color_green}Wi-Fi Support: {color_reset}{json_data['wifi_support']}")
    except Exception as e:
        print(f"{color_red}Error printing board information: {e}{color_reset}")

def setup_wifi():
    import network
    ssid, password = load_wifi_credentials()
    if ssid is None or password is None:
        ssid = input("Enter Wi-Fi SSID: ")
        password = input("Enter Wi-Fi password: ")
        save_wifi_credentials(ssid, password)
        ssid, password = load_wifi_credentials()  # Reload credentials

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    time.sleep(1)
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
    else:
        print(f"{color_red}Failed to connect to Wi-Fi{color_reset}")

# Example usage
info = detect_board()
save_setup_info(info)
print_colored_info(info)

if info['wifi_support'] == 'yes':
    setup_wifi()
else:
    print(f"{color_red}Wi-Fi not supported on this board, skipping installation!{color_reset}")
