import ujson as json
import machine
import uos as os
import gc
import usocket as socket
import time

# Constants
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_CYAN = "\033[96m"
MAIN_DIR = "Star-Os"
STAROS_FILE = f"{MAIN_DIR}/Star-Os.py"
INDEX_FILE = f"{MAIN_DIR}/index.html"
VERSION_FILE = f"{MAIN_DIR}/version.json"
GITHUB_REPO = "Andre-cmd-rgb/Star-Os-Micropython"
BRANCH = "main"

gc.enable()
gc.collect()

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

def file_exists(file_path):
    """Checks if the specified file exists."""
    try:
        with open(file_path, 'r'):
            pass
        return True
    except OSError:
        return False

def download_file(url, file_path):
    """Downloads a file from the specified URL."""
    import urequests
    retries = 3
    while retries > 0:
        try:
            response = urequests.get(url)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"{COLOR_GREEN}Downloaded: {file_path}{COLOR_RESET}")
                gc.collect()
                return True
            else:
                print(f"{COLOR_RED}Failed to download {file_path}: {response.status_code}{COLOR_RESET}")
                retries -= 1
        except OSError as e:
            print(f"{COLOR_RED}Error downloading {file_path}: {e}{COLOR_RESET}")
            retries -= 1
        finally:
            if 'response' in locals():
                response.close()

    if retries == 0:
        print(f"{COLOR_RED}Max retries exceeded for {file_path}. Skipping.{COLOR_RESET}")
        return False

def get_latest_commit():
    """Gets the latest commit hash from GitHub."""
    import urequests
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/{BRANCH}"
    try:
        response = urequests.get(url)
        if response.status_code == 200:
            commit_data = response.json()
            return commit_data['sha']
        else:
            print(f"{COLOR_RED}Failed to get latest commit: {response.status_code}{COLOR_RESET}")
            return None
    except OSError as e:
        print(f"{COLOR_RED}Error getting latest commit: {e}{COLOR_RESET}")
        return None
    finally:
        if 'response' in locals():
            response.close()

def update_files():
    """Checks for updates and updates files if necessary."""
    ensure_directory_exists(MAIN_DIR)
    latest_commit = get_latest_commit()
    if latest_commit:
        version_info = load_version_info()
        if version_info.get('latest_commit') != latest_commit:
            print(f"{COLOR_YELLOW}New update available. Updating files...{COLOR_RESET}")
            # Delete old files
            try:
                os.remove(STAROS_FILE)
                os.remove(INDEX_FILE)
            except OSError as e:
                print(f"{COLOR_RED}Error deleting old files: {e}{COLOR_RESET}")
            
            # Download new files
            staros_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}/Src/Star-Os.py"
            index_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}/Src/index.html"
            download_file(staros_url, STAROS_FILE)
            download_file(index_url, INDEX_FILE)

            # Update version info with latest commit hash
            version_info['latest_commit'] = latest_commit
            save_version_info(version_info)

            print(f"{COLOR_GREEN}Update completed, rebooting...{COLOR_RESET}")
            time.sleep(2)
            machine.reset()
        else:
            print(f"{COLOR_GREEN}No updates available. Running current version.{COLOR_RESET}")
    else:
        print(f"{COLOR_RED}Could not retrieve latest commit. Skipping update.{COLOR_RESET}")

def load_version_info():
    """Loads version information from the version file."""
    try:
        with open(VERSION_FILE, "r") as f:
            return json.load(f)
    except OSError as e:
        print(f"{COLOR_YELLOW}Version file not found or invalid, creating new file.{COLOR_RESET}")
        return {}

def save_version_info(version_info):
    """Saves version information to the version file."""
    try:
        with open(VERSION_FILE, "w") as f:
            json.dump(version_info, f)
    except OSError as e:
        print(f"{COLOR_RED}Error saving version info: {e}{COLOR_RESET}")

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
    

    if file_exists(STAROS_FILE):
        print(f"{COLOR_GREEN}Checking for updates...{COLOR_RESET}")
        update_files()
        print(f"{COLOR_BLUE}Star-Os.py found. Running the script...{COLOR_RESET}")
        try:
            exec(open(STAROS_FILE).read())
        except Exception as e:
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
            repo = GITHUB_REPO
            file_list = ["Src/Star-Os.py", "Src/index.html"]
            download_files_from_github(repo, file_list, MAIN_DIR)
            gc.collect()
            download_files_from_github("miguelgrinberg/microdot", ["src/microdot.py", "src/microdot_asyncio.py"], "lib", "v1")
            print(f"{COLOR_GREEN}Star Os installation completed successfully, rebooting...{COLOR_RESET}")
            gc.collect()
            machine.reset()
        else:
            print(f"{COLOR_RED}Wi-Fi not supported on this board, skipping installation!{COLOR_RESET}")

if __name__ == "__main__":
    gc.collect()
    main()
