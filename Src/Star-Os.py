import ujson
import gc
import time
import machine
import network
import uos
import sys
from microdot_asyncio import Microdot, Response, send_file
from updater import Updater


# Initialize the updater
updater = Updater(
    user="Andre-cmd-rgb",
    repo="Star-Os-Micropython",
    branch="main",  # Specify the branch of your repository
    dest_dir="/Star-Os",  # Specify the destination directory where files should be saved
    files=["Star-Os.py", "index.html"],  # List of files to include in the OTA update
)

# Constants
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_BLUE = "\033[94m"
COLOR_YELLOW = "\033[93m"
MAIN_DIR = "Star-Os"
DYNAMIC_ROUTES_FILE = f"{MAIN_DIR}/dynamic_routes.json"
CONFIG_FILE = f"{MAIN_DIR}/config.json"

gc.enable()
gc.collect()
def load_wifi_credentials():
    """Loads Wi-Fi credentials from the saved JSON file."""
    gc.collect()
    try:
        with open(f"{MAIN_DIR}/wifi-credentials.json", "r") as f:
            wifi_credentials = ujson.load(f)
        return wifi_credentials.get('ssid'), wifi_credentials.get('password')
    except OSError as e:
        print(f"{COLOR_RED}Error loading Wi-Fi credentials: {e}{COLOR_RESET}")
        return None, None

def save_dynamic_routes(routes):
    """Saves dynamic routes to a JSON file."""
    gc.collect()
    try:
        with open(DYNAMIC_ROUTES_FILE, "w") as f:
            ujson.dump(routes, f)
    except OSError as e:
        print(f"{COLOR_RED}Error saving dynamic routes: {e}{COLOR_RESET}")

def load_dynamic_routes():
    """Loads dynamic routes from the saved JSON file."""
    gc.collect()
    try:
        with open(DYNAMIC_ROUTES_FILE, "r") as f:
            return ujson.load(f)
    except OSError as e:
        print(f"{COLOR_YELLOW}Dynamic routes file not found or invalid, creating new file.{COLOR_RESET}")
        # Create a new empty file if it doesn't exist or is invalid
        save_dynamic_routes({})
        return {}

def connect_to_wifi(ssid, password):
    """Connects to the Wi-Fi using the provided SSID and password."""
    gc.collect()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    time.sleep(1)
    wlan.config(pm=wlan.PM_NONE)
    gc.collect()
    print(f"{COLOR_BLUE}Connecting to Wi-Fi...{COLOR_RESET}")
    wlan.connect(ssid, password)
    gc.collect()
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
        gc.collect()
        return True
    else:
        print(f"{COLOR_RED}Failed to connect to Wi-Fi, rebooting...{COLOR_RESET}")
        machine.reset()
        return False

def handle_dynamic_route(request, path, routes):
    """Handles dynamic route requests."""
    gc.collect()
    if path in routes:
        return routes[path]
    return 'Route not found.', 404

def main_operations(app, routes):
    """Configures and runs the main operations of the Star-OS system."""
    print(f"{COLOR_BLUE}Star-OS started successfully!{COLOR_RESET}")
    gc.collect()

    @app.route('/')
    async def index(request):
        return send_file(MAIN_DIR + '/index.html')

    @app.route('/shutdown')
    def shutdown(request):
        request.app.shutdown()
        return 'The server is shutting down...'

    @app.route('/status', methods=['POST'])
    async def status(request):
        return Response('{"status": "up"}', headers={'Content-Type': 'application/json'})
    
    @app.route('/create', methods=['POST'])
    async def create_route(request):
        data = ujson.loads(request.body)
        path = data.get('path')
        response = data.get('response')

        if path and response:
            routes[path.strip('/')] = response
            save_dynamic_routes(routes)  # Save routes to file
            return 'Route created successfully.', 201
        return 'Invalid data.', 400

    @app.route('/delete', methods=['POST'])
    async def delete_route(request):
        data = ujson.loads(request.body)
        path = data.get('path')

        if path and path.strip('/') in routes:
            del routes[path.strip('/')]
            save_dynamic_routes(routes)  # Save routes to file
            return 'Route deleted successfully.', 200
        return 'Route not found.', 404

    @app.route('/routes', methods=['GET'])
    async def list_routes(request):
        return Response(ujson.dumps(routes))

    @app.route('/<path:path>')
    async def dynamic_route(request, path):
        return handle_dynamic_route(request, path, routes)
    
    @app.errorhandler(404)
    async def not_found(request):
        return 'Not found'
    gc.collect()
    app.run(host='0.0.0.0', port=80, debug=True)

def ensure_directory_exists(directory):
    """Ensures the specified directory exists."""
    gc.collect()
    try:
        uos.listdir(directory)
    except OSError:
        uos.mkdir(directory)

def file_exists(file_path):
    """Checks if the specified file exists."""
    gc.collect()
    try:
        with open(file_path, 'r'):
            pass
        return True
    except OSError:
        return False

def load_config():
    """Loads configuration settings from the config file."""
    gc.collect()
    try:
        with open(CONFIG_FILE, "r") as f:
            return ujson.load(f)
    except OSError as e:
        print(f"{COLOR_YELLOW}Config file not found or invalid, creating new file.{COLOR_RESET}")
        return {}

def save_config(config):
    """Saves configuration settings to the config file."""
    gc.collect()
    try:
        with open(CONFIG_FILE, "w") as f:
            ujson.dump(config, f)
    except OSError as e:
        print(f"{COLOR_RED}Error saving config: {e}{COLOR_RESET}")

def prompt_user_for_mode():
    """Prompts the user to choose the mode (server or slave) and saves it to the config file."""
    gc.collect()
    config = load_config()
    if 'mode' not in config:
        while True:
            mode = input("Do you want to run this as a server or a slave? (Enter 'server' or 'slave'): ").strip().lower()
            if mode in ['server', 'slave']:
                config['mode'] = mode
                save_config(config)
                break
            else:
                print(f"{COLOR_RED}Invalid input. Please enter 'server' or 'slave'.{COLOR_RESET}")
    return config['mode']

def main():
    """Main function to load credentials, connect to Wi-Fi, and run operations."""
    gc.collect()
    ensure_directory_exists(MAIN_DIR)

    mode = prompt_user_for_mode()
    print(f"{COLOR_GREEN}Running in {mode} mode.{COLOR_RESET}")
    gc.collect()
    ssid, password = load_wifi_credentials()
    if ssid and password:
        if connect_to_wifi(ssid, password):
            gc.collect()
            print(f"{COLOR_GREEN}Checking for updates...{COLOR_RESET}")
            gc.collect()
            # Check if newer version is available
            if updater.fetch():
                gc.collect()
                print("Newer version available. Updating...")

                # Perform the update
                if updater.update():
                    gc.collect()
                    print("Update successful.")
                else:
                    gc.collect()
                    print("Update failed.")
            else:
                gc.collect()
                print("No newer version available.")
            gc.collect()
            app = Microdot()
            routes = load_dynamic_routes()
            main_operations(app, routes)
        else:
            print(f"{COLOR_RED}Unable to proceed without Wi-Fi connection.{COLOR_RESET}")
    else:
        print(f"{COLOR_RED}Wi-Fi credentials not found or invalid.{COLOR_RESET}")

if __name__ == "__main__":
    gc.collect()
    main()