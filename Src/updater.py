import machine
import ujson as json
import uos as os
import usocket as socket
import time
import gc

# Constants
COLOR_RESET = "\\033[0m"
COLOR_RED = "\\033[91m"
COLOR_GREEN = "\\033[92m"
COLOR_YELLOW = "\\033[93m"
COLOR_BLUE = "\\033[94m"

MAIN_DIR = "Star-Os"
STAROS_FILE = f"{MAIN_DIR}/Star-Os.py"
INDEX_FILE = f"{MAIN_DIR}/index.html"
VERSION_FILE = f"{MAIN_DIR}/version.json"
GITHUB_REPO = "Andre-cmd-rgb/Star-Os-Micropython"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

gc.enable()
gc.collect()

def ensure_directory_exists(directory):
    """Ensures that the directory exists."""
    gc.collect()
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
    gc.collect()
    try:
        with open(file_path, 'r'):
            pass
        return True
    except OSError:
        return False

def download_file(url, file_path):
    """Downloads a file from the specified URL."""
    import urequests
    gc.collect()
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

def get_latest_release():
    """Gets the latest release information from GitHub."""
    import urequests
    gc.collect()
    try:
        response = urequests.get(GITHUB_API_URL)
        if response.status_code == 200:
            release_data = response.json()
            return release_data
        else:
            print(f"{COLOR_RED}Failed to get latest release: {response.status_code}{COLOR_RESET}")
            return None
    except Exception as e:
        print(f"{COLOR_RED}Error getting latest release: {e}{COLOR_RESET}")
        return None
    finally:
        if 'response' in locals():
            response.close()

def update_files():
    """Checks for updates and updates files if necessary."""
    ensure_directory_exists(MAIN_DIR)
    gc.collect()
    release_data = get_latest_release()
    gc.collect()
    if release_data:
        latest_commit = release_data['tag_name']
        version_info = load_version_info()
        if version_info.get('latest_commit') != latest_commit:
            print(f"{COLOR_YELLOW}New update available. Updating files...{COLOR_RESET}")
            gc.collect()
            assets = release_data['assets']
            gc.collect()
            staros_asset = next((asset for asset in assets if asset['name'] == 'Star-Os.py'), None)
            index_asset = next((asset for asset in assets if asset['name'] == 'index.html'), None)

            if staros_asset and index_asset:
                gc.collect()
                download_file(staros_asset['browser_download_url'], STAROS_FILE)
                gc.collect()
                download_file(index_asset['browser_download_url'], INDEX_FILE)
                gc.collect()
                version_info['latest_commit'] = latest_commit
                save_version_info(version_info)
                
                print(f"{COLOR_GREEN}Update completed, rebooting...{COLOR_RESET}")
                gc.collect()
                time.sleep(2)
                machine.reset()
            else:
                print(f"{COLOR_RED}Required assets not found in the latest release.{COLOR_RESET}")
        else:
            print(f"{COLOR_GREEN}No updates available. Running current version.{COLOR_RESET}")
    else:
        print(f"{COLOR_RED}Could not retrieve latest release. Skipping update.{COLOR_RESET}")

def load_version_info():
    """Loads version information from the version file."""
    gc.collect()
    try:
        with open(VERSION_FILE, "r") as f:
            return json.load(f)
    except OSError as e:
        print(f"{COLOR_YELLOW}Version file not found or invalid, creating new file.{COLOR_RESET}")
        return {}

def save_version_info(version_info):
    """Saves version information to the version file."""
    gc.collect()
    try:
        with open(VERSION_FILE, "w") as f:
            json.dump(version_info, f)
    except OSError as e:
        print(f"{COLOR_RED}Error saving version info: {e}{COLOR_RESET}")

def check_for_updates():
    gc.collect()
    print(f"{COLOR_GREEN}Checking for updates...{COLOR_RESET}")
    update_files()