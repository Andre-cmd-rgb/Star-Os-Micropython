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
    from microdot_asyncio import Microdot, send_file
    import ujson

    print(f"{COLOR_BLUE}Star-OS started successfully!{COLOR_RESET}")

    # Initialize the web server
    app = Microdot()

    dynamic_apps = {}

    @app.route('/')
    async def index(request):
        return '''
            <html>
                <body>
                    <h1>Create New API</h1>
                    <form action="/create-api" method="post">
                        <label for="port">Port:</label>
                        <input type="number" id="port" name="port"><br>
                        <label for="path">Path:</label>
                        <input type="text" id="path" name="path"><br>
                        <label for="response">Response:</label>
                        <textarea id="response" name="response"></textarea><br>
                        <input type="submit" value="Create API">
                    </form>
                </body>
            </html>
        '''

    @app.post('/create-api')
    async def create_api(request):
        data = await request.form()
        port = int(data['port'])
        path = data['path']
        response = data['response']

        if port not in dynamic_apps:
            dynamic_app = Microdot()
            dynamic_apps[port] = dynamic_app

            @dynamic_app.route('/<path:path>', methods=['GET', 'POST'])
            async def dynamic_route(request, path):
                if request.method == 'POST':
                    return ujson.loads(response)
                return response

            dynamic_app.run(host='0.0.0.0', port=port, debug=True)
        else:
            dynamic_app = dynamic_apps[port]

            @dynamic_app.route(path, methods=['GET', 'POST'])
            async def new_route(request):
                if request.method == 'POST':
                    return ujson.loads(response)
                return response

        return f'API created at port {port} with path {path}'

    @app.get('/shutdown')
    async def shutdown(request):
        request.app.shutdown()
        return 'The server is shutting down...'

    print(f"{COLOR_GREEN}Web Server started!{COLOR_RESET}")
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
