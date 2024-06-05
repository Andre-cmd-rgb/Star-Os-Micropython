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

gc.enable()

def detect_board():
    """Detects and returns information about the board."""
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
    """Saves the detected board information to a JSON file."""
    try:
        with open("setupinfo.json", "w") as f:
            json.dump(board_info, f)
    except Exception as e:
        print(f"{color_red}Error saving setup info: {e}{color_reset}")

def save_wifi_credentials(ssid, password):
    """Saves Wi-Fi credentials to a JSON file."""
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
    """Loads Wi-Fi credentials from the saved JSON file."""
    try:
        with open(f"{MainDir}/wifi-credentials.json", "r") as f:
            wifi_credentials = json.load(f)
        return wifi_credentials['ssid'], wifi_credentials['password']
    except (OSError, ValueError, KeyError) as e:
        return None, None

def print_colored_info():
    """Prints the board information in colored text."""
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

def setup_wifi(info):
    """Sets up the Wi-Fi connection."""
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
    else:
        print(f"{color_red}Failed to connect to Wi-Fi{color_reset}")
        if info['board'] == 'Arduino Portenta H7 with STM32H747':
            # Rebooting only if board is Portenta H7 because the Wi-Fi works one time out of 2
            machine.reset()

def ensure_directories_exist(filepath):
    """Ensure all directories in the given file path exist."""
    directories = filepath.split('/')[:-1]
    current_path = ''
    for directory in directories:
        current_path = f"{current_path}/{directory}".strip('/')
        if current_path not in os.listdir():
            os.mkdir(current_path)

def ensure_directory_exists(directory):
    """Ensures that the directory exists."""
    try:
        os.listdir(directory)
    except OSError:
        try:
            os.mkdir(directory)
        except OSError as e:
            print(f"Error creating directory {directory}: {e}")
            raise

def download_files_from_github(repo, file_list, dest_dir):
    import urequests
    """Downloads specified files from a GitHub repository and saves them directly to dest_dir."""
    base_url = f"https://raw.githubusercontent.com/{repo}/master/"



    # Ensure dest_dir exists
    try:
        ensure_directory_exists(dest_dir)
    except OSError:
        return

    for file in file_list:
        url = f"{base_url}{file}"
        filename = file.split('/')[-1]
        file_path = f"{dest_dir}/{filename}"

        # Check if file already exists
        if filename in os.listdir(dest_dir):
            print(f"{color_red}File {filename} already exists in {dest_dir}. Skipping.{color_reset}")
            continue

        retries = 3
        while retries > 0:
            try:
                response = urequests.get(url)
                if response.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    print(f"{color_green}Downloaded: {filename}{color_reset}")
                    break
                else:
                    print(f"{color_red}Failed to download {filename}: {response.status_code}{color_reset}")
                    retries -= 1
            except OSError as e:
                print(f"{color_red}Error downloading {filename}: {e}{color_reset}")
                retries -= 1
            finally:
                if 'response' in locals():
                    response.close()
        
        if retries == 0:
            print(f"{color_red}Max retries exceeded for {filename}. Skipping.{color_reset}")
def main():
    if MainDir in os.listdir() and "Star-Os.py" in os.listdir(MainDir):
        print(f"{color_yellow}Star-Os.py found. Running the script...{color_reset}")
        try:
            exec(open(f"{MainDir}/Star-Os.py").read())
        except Exception as e:
            print(f"{color_red}Error running Star-Os.py: {e}{color_reset}")
    else:
        info = detect_board()
        save_setup_info(info)
        print_colored_info()

        if info['wifi_support'] == 'yes':
            setup_wifi(info)
            import mip
            mip.install("urequests")
            # Example usage for downloading files from GitHub
            repo = "Andre-cmd-rgb/Star-Os-Micropython"
            file_list = ["Src/Star-Os.py"]
            download_files_from_github(repo, file_list, MainDir)
            download_files_from_github("miguelgrinberg/microdot", ["src/microdot/microdot.py", "src/microdot/__init__.py"], "lib/microdot")
            print(f"{color_green}Star Os installation completed succesfully!, rebooting...{color_reset}")
            machine.reset()
        else:
            print(f"{color_red}Wi-Fi not supported on this board, skipping installation!{color_reset}")

if __name__ == "__main__":
    main()
