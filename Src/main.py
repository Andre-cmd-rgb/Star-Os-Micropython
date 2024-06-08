import json
import machine
import os
import gc
import time

# ANSI escape codes for colors
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_CYAN = "\033[96m"

# Main directory for storing Wi-Fi credentials
MAIN_DIR = "Star-Os"

gc.enable()
gc.collect()
def detect_board():
    """Detects and returns information about the board."""
    board_info = {}

    try:
        freq = machine.freq()
        if isinstance(freq, tuple):
            board_info['freq'] = ' / '.join(f'{f // 10**6} MHz' for f in freq)
        else:
            board_info['freq'] = f'{freq // 10**6} MHz'
    except Exception as e:
        board_info['freq'] = "Unknown"
        print(f"{COLOR_RED}Error retrieving frequency: {e}{COLOR_RESET}")

    try:
        uname = os.uname()
        board_info['board'] = uname.machine
        board_info['version'] = uname.version
        board_info['release'] = uname.release
    except AttributeError:
        board_info['board'] = "Unknown"
        board_info['version'] = "Unknown"
        board_info['release'] = "Unknown"
        print(f"{COLOR_RED}Error retrieving uname information{COLOR_RESET}")

    try:
        board_info['mem_free'] = gc.mem_free()
        board_info['mem_alloc'] = gc.mem_alloc()
    except Exception as e:
        board_info['mem_free'] = "Unknown"
        board_info['mem_alloc'] = "Unknown"
        print(f"{COLOR_RED}Error retrieving memory information: {e}{COLOR_RESET}")

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
        print(f"{COLOR_RED}Error saving setup info: {e}{COLOR_RESET}")

def save_wifi_credentials(ssid, password):
    """Saves Wi-Fi credentials to a JSON file."""
    wifi_credentials = {
        'ssid': ssid,
        'password': password
    }
    try:
        if MAIN_DIR not in os.listdir():
            os.mkdir(MAIN_DIR)
        with open(f"{MAIN_DIR}/wifi-credentials.json", "w") as f:
            json.dump(wifi_credentials, f)
    except Exception as e:
        print(f"{COLOR_RED}Error saving Wi-Fi credentials: {e}{COLOR_RESET}")

def load_wifi_credentials():
    """Loads Wi-Fi credentials from the saved JSON file."""
    try:
        with open(f"{MAIN_DIR}/wifi-credentials.json", "r") as f:
            wifi_credentials = json.load(f)
        return wifi_credentials['ssid'], wifi_credentials['password']
    except (OSError, ValueError, KeyError) as e:
        return None, None

def print_colored_info():
    """Prints the board information in colored text."""
    try:
        with open("setupinfo.json", "r") as f:
            json_data = json.load(f)

        print(f"{COLOR_CYAN}Board Information:{COLOR_RESET}")
        print(f"{COLOR_GREEN}Board: {COLOR_RESET}{json_data['board']}")
        print(f"{COLOR_GREEN}Micropython Version: {COLOR_RESET}{json_data['version']}")
        print(f"{COLOR_GREEN}Micropython Release: {COLOR_RESET}{json_data['release']}")
        print(f"{COLOR_GREEN}CPU Frequency: {COLOR_RESET}{json_data['freq']}")
        print(f"{COLOR_GREEN}Free Memory: {COLOR_RESET}{json_data['mem_free']} bytes")
        print(f"{COLOR_GREEN}Allocated Memory: {COLOR_RESET}{json_data['mem_alloc']} bytes")
        print(f"{COLOR_GREEN}Wi-Fi Support: {COLOR_RESET}{json_data['wifi_support']}")
    except Exception as e:
        print(f"{COLOR_RED}Error printing board information: {e}{COLOR_RESET}")

def setup_wifi(info):
    """Sets up the Wi-Fi connection."""
    import network
    ssid, password = load_wifi_credentials()
    if ssid is None or password is None:
        ssid = input("Enter Wi-Fi SSID: ")
        password = input("Enter Wi-Fi password: ")
        save_wifi_credentials(ssid, password)
        ssid, password = load_wifi_credentials()

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    time.sleep(1)
    wlan.config(pm=wlan.PM_NONE)
    print(f"{COLOR_BLUE}Connecting to Wi-Fi...{COLOR_RESET}")
    wlan.connect(ssid, password)

    max_wait = 10
    while max_wait > 0:
        if wlan.isconnected():
            break
        time.sleep(1)
        max_wait -= 1

    if wlan.isconnected():
        print(f"{COLOR_GREEN}Wi-Fi connected!{COLOR_RESET}")
        print(wlan.ifconfig())
    else:
        print(f"{COLOR_RED}Failed to connect to Wi-Fi{COLOR_RESET}")
        if info['board'] == 'Arduino Portenta H7 with STM32H747':
            machine.reset()

def ensure_directory_exists(directory):
    """Ensures that the directory exists."""
    try:
        os.listdir(directory)
    except OSError:
        try:
            os.mkdir(directory)
        except OSError as e:
            print(f"{COLOR_RED}Error creating directory {directory}: {e}{COLOR_RESET}")
            raise

def download_files_from_github(repo, file_list, dest_dir, branch="master"):
    """Downloads specified files from a GitHub repository and saves them directly to dest_dir."""
    import urequests
    base_url = f"https://raw.githubusercontent.com/{repo}/{branch}/"

    try:
        ensure_directory_exists(dest_dir)
    except OSError:
        return

    for file in file_list:
        url = f"{base_url}{file}"
        filename = file.split('/')[-1]
        file_path = f"{dest_dir}/{filename}"

        if filename in os.listdir(dest_dir):
            print(f"{COLOR_RED}File {filename} already exists in {dest_dir}. Skipping.{COLOR_RESET}")
            continue

        retries = 3
        while retries > 0:
            try:
                response = urequests.get(url)
                if response.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    print(f"{COLOR_GREEN}Downloaded: {filename}{COLOR_RESET}")
                    gc.collect()
                    break
                else:
                    print(f"{COLOR_RED}Failed to download {filename}: {response.status_code}{COLOR_RESET}")
                    retries -= 1
            except OSError as e:
                print(f"{COLOR_RED}Error downloading {filename}: {e}{COLOR_RESET}")
                retries -= 1
            finally:
                if 'response' in locals():
                    response.close()

        if retries == 0:
            print(f"{COLOR_RED}Max retries exceeded for {filename}. Skipping.{COLOR_RESET}")

def main():
    if MAIN_DIR in os.listdir() and "Star-Os.py" in os.listdir(MAIN_DIR):
        print(f"{COLOR_YELLOW}Star-Os.py found. Running the script...{COLOR_RESET}")
        gc.collect()
        try:
            gc.collect()
            exec(open(f"{MAIN_DIR}/Star-Os.py").read())
        except Exception as e:
            gc.collect()
            print(f"{COLOR_RED}Error running Star-Os.py: {e}{COLOR_RESET}")
    else:
        info = detect_board()
        save_setup_info(info)
        print_colored_info()

        if info['wifi_support'] == 'yes':
            setup_wifi(info)
            import mip
            mip.install("urequests")
            gc.collect()
            repo = "Andre-cmd-rgb/Star-Os-Micropython"
            file_list = ["Src/Star-Os.py", "Src/index.html"]
            download_files_from_github(repo, file_list, MAIN_DIR)
            gc.collect()
            download_files_from_github("miguelgrinberg/microdot", ["src/microdot.py", "src/microdot_asyncio.py"], "lib", "v1")
            gc.collect()
            download_files_from_github("Andre-cmd-rgb/Star-Os-Micropython", ["Src/updater.py"], "lib")
            gc.collect()
            print(f"{COLOR_GREEN}Star Os installation completed successfully, rebooting...{COLOR_RESET}")
            gc.collect()
            machine.reset()
        else:
            print(f"{COLOR_RED}Wi-Fi not supported on this board, skipping installation!{COLOR_RESET}")

if __name__ == "__main__":
    gc.collect()
    main()