import ujson
import gc
import time
import machine
import network
from microdot_asyncio import Microdot, Response, send_file

# Constants
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_BLUE = "\033[94m"
COLOR_YELLOW = "\033[93m"
MAIN_DIR = "Star-Os"
DYNAMIC_ROUTES_FILE = f"{MAIN_DIR}/dynamic_routes.json"

gc.enable()

def load_wifi_credentials():
    """Loads Wi-Fi credentials from the saved JSON file."""
    try:
        with open(f"{MAIN_DIR}/wifi-credentials.json", "r") as f:
            wifi_credentials = ujson.load(f)
        return wifi_credentials.get('ssid'), wifi_credentials.get('password')
    except OSError as e:
        print(f"{COLOR_RED}Error loading Wi-Fi credentials: {e}{COLOR_RESET}")
        return None, None

def save_dynamic_routes(routes):
    """Saves dynamic routes to a JSON file."""
    try:
        with open(DYNAMIC_ROUTES_FILE, "w") as f:
            ujson.dump(routes, f)
    except OSError as e:
        print(f"{COLOR_RED}Error saving dynamic routes: {e}{COLOR_RESET}")

def load_dynamic_routes():
    """Loads dynamic routes from the saved JSON file."""
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

def handle_dynamic_route(request, path, routes):
    """Handles dynamic route requests."""
    if path in routes:
        return routes[path]
    return 'Route not found.', 404

def main_operations(app, routes):
    """Configures and runs the main operations of the Star-OS system."""
    print(f"{COLOR_BLUE}Star-OS started successfully!{COLOR_RESET}")

    @app.route('/')
    async def index(request):
        return send_file(MAIN_DIR + '/index.html')
    
    @app.route('/shutdown')
    def shutdown(request):
        request.app.shutdown()
        return 'The server is shutting down...'
    
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

    

    app.run(host='0.0.0.0', port=80, debug=True)

def main():
    """Main function to load credentials, connect to Wi-Fi, and run operations."""
    ssid, password = load_wifi_credentials()
    if ssid and password:
        if connect_to_wifi(ssid, password):
            app = Microdot()
            routes = load_dynamic_routes()
            main_operations(app, routes)
        else:
            print(f"{COLOR_RED}Unable to proceed without Wi-Fi connection.{COLOR_RESET}")
    else:
        print(f"{COLOR_RED}Wi-Fi credentials not found or invalid.{COLOR_RESET}")

if __name__ == "__main__":
    main()
