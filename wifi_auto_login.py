import sqlite3
import requests
import datetime
import re
import argparse
import json
import os


# --- CONFIGURATION ---
CONFIG_PATH = "config.json"

def load_config():
    """Load configuration file and return config dict"""
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(
            "Missing config.json. Please copy config.example.json to config.json and fill in your details."
        )
    
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    
    return config

# Initialize logging first
from config.logging_config import setup_logging_from_env, get_logger
setup_logging_from_env()
logger = get_logger(__name__)

# Import network utilities for multi-network support
try:
    from network_utils import NetworkProfileManager, get_current_ssid
    MULTI_NETWORK_SUPPORT = True
    logger.info("Multi-network support enabled")
except ImportError as e:
    logger.warning(f"Multi-network support disabled: {e}")
    MULTI_NETWORK_SUPPORT = False

# Global variables - will be loaded when needed
URL = None
USERNAME = None
PASSWORD = None
PRODUCT_TYPE = None

# --- DATABASE SETUP ---
DB_NAME = "wifi_log.db"

def setup_database():
    """Create the database and table if they do not exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if the table exists and get its schema
    cursor.execute("PRAGMA table_info(login_attempts)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if not columns:
        # Create new table with network support
        cursor.execute("""
            CREATE TABLE login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                network_name TEXT,
                network_ssid TEXT,
                username TEXT,
                password TEXT,
                a TEXT,
                response_status TEXT,
                response_message TEXT
            )
        """)
        logger.info("Created new login_attempts table with network support")
    else:
        # Check if we need to add network columns to existing table
        if 'network_name' not in columns:
            cursor.execute("ALTER TABLE login_attempts ADD COLUMN network_name TEXT")
            logger.info("Added network_name column to existing table")
        
        if 'network_ssid' not in columns:
            cursor.execute("ALTER TABLE login_attempts ADD COLUMN network_ssid TEXT")
            logger.info("Added network_ssid column to existing table")
    conn.commit()
    conn.close()

def log_attempt(username, password, a, response_status, response_message, network_name=None, network_ssid=None):
    """Log each login attempt in the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO login_attempts (timestamp, network_name, network_ssid, username, password, a, response_status, response_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (datetime.datetime.now(), network_name, network_ssid, username, "******", a, response_status, response_message))
    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS ---
def extract_message(response_text):
    """Extracts the meaningful message from the XML response."""
    match = re.search(r"<message><!\[CDATA\[(.*?)\]\]></message>", response_text)
    return match.group(1) if match else "Unknown response"

# --- MAIN WIFI LOGIN FUNCTION ---
def wifi_login(network_name=None):
    """Perform the WiFi login request and log the result."""
    network_profile_name = "legacy"
    network_ssid = "Unknown"
    
    try:
        if MULTI_NETWORK_SUPPORT:
            # Use multi-network configuration
            manager = NetworkProfileManager()
            network_profile_name, network_config = manager.get_network_profile(network_name, auto_detect=True)
            network_ssid = network_config.get("ssid", "Unknown")
            
            URL = network_config["wifi_url"]
            USERNAME = network_config["username"]
            PASSWORD = network_config["password"]
            PRODUCT_TYPE = network_config.get("product_type", "0")
            
            print(f"\n🌐 Using Network Profile: {network_profile_name}")
            print(f"📡 Network SSID: {network_ssid}")
            print(f"🔗 Login URL: {URL}")
        else:
            # Fallback to legacy single network configuration
            config = load_config()
            URL = config["wifi_url"]
            USERNAME = config["username"]
            PASSWORD = config["password"]
            PRODUCT_TYPE = config.get("product_type", "0")
            network_ssid = config.get("ssid", "Unknown")
            print(f"\n🌐 Using Legacy Configuration")
    
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        print(f"❌ Configuration Error: {e}")
        return
    
    a_value = str(int(datetime.datetime.now().timestamp()))  # Generate dynamic 'a' value

    payload = {
        "mode": "191",
        "username": USERNAME,
        "password": PASSWORD,
        "a": a_value,
        "producttype": PRODUCT_TYPE
    }

    try:
        response = requests.post(URL, data=payload)
        response_status = response.status_code
        response_message = extract_message(response.text)

        print(f"\n📌 Login Attempt")
        print(f"Time: {datetime.datetime.now()}")
        print(f"Username: {USERNAME}")
        print(f"Session ID (a): {a_value}")
        print(f"Status: {response_status}")
        print(f"Message: {response_message}")
        print("-" * 80)

        # Log the attempt in SQLite with network information
        log_attempt(USERNAME, PASSWORD, a_value, response_status, response_message, 
                   network_profile_name, network_ssid)

    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        log_attempt(USERNAME, PASSWORD, a_value, "FAILED", str(e), 
                   network_profile_name, network_ssid)

# --- VIEW LOGIN LOGS ---
def view_logs(limit=5, network_filter=None):
    """Display login logs in a readable format."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if table has new network columns
    cursor.execute("PRAGMA table_info(login_attempts)")
    columns = [row[1] for row in cursor.fetchall()]
    has_network_columns = 'network_name' in columns and 'network_ssid' in columns
    
    if has_network_columns:
        base_query = """
            SELECT timestamp, network_name, network_ssid, username, a, response_status, response_message 
            FROM login_attempts 
        """
        if network_filter:
            query = base_query + "WHERE network_name = ? ORDER BY timestamp DESC LIMIT ?"
            cursor.execute(query, (network_filter, limit))
        else:
            query = base_query + "ORDER BY timestamp DESC LIMIT ?"
            cursor.execute(query, (limit,))
    else:
        # Legacy table structure
        cursor.execute("""
            SELECT timestamp, username, a, response_status, response_message 
            FROM login_attempts 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))

    logs = cursor.fetchall()
    conn.close()

    if not logs:
        filter_msg = f" for network '{network_filter}'" if network_filter else ""
        logger.info(f"No login attempts found in database{filter_msg}")
        return

    filter_msg = f" for network '{network_filter}'" if network_filter else ""
    logger.info(f"Recent login attempts retrieved from database{filter_msg}")
    logger.info("=" * 80)

    for log in logs:
        if has_network_columns:
            timestamp, network_name, network_ssid, username, a, status, message = log
            logger.info(f"Time: {timestamp}")
            logger.info(f"Network: {network_name} ({network_ssid})")
            logger.info(f"Username: {username}")
            logger.info(f"Session ID (a): {a}")
            logger.info(f"Status: {status}")
            logger.info(f"Message: {message}")
        else:
            timestamp, username, a, status, message = log
            logger.info(f"Time: {timestamp}")
            logger.info(f"Username: {username}")
            logger.info(f"Session ID (a): {a}")
            logger.info(f"Status: {status}")
            logger.info(f"Message: {message}")
        logger.info("-" * 80)

def parse_arguments():
    """Parse command line arguments for logging configuration."""
    parser = argparse.ArgumentParser(description='WiFi Auto Login with Professional Logging')

    # Logging configuration arguments
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level (default: INFO)'
    )
    parser.add_argument(
        '--log-file',
        action='store_true',
        default=True,
        help='Enable file logging (default: enabled)'
    )
    parser.add_argument(
        '--no-log-file',
        action='store_false',
        dest='log_file',
        help='Disable file logging'
    )
    parser.add_argument(
        '--log-dir',
        default='./logs',
        help='Directory for log files (default: ./logs)'
    )
    parser.add_argument(
        '--console-logging',
        action='store_true',
        default=True,
        help='Enable console logging (default: enabled)'
    )
    parser.add_argument(
        '--no-console-logging',
        action='store_false',
        dest='console_logging',
        help='Disable console logging'
    )

    # Application arguments
    parser.add_argument(
        '--view-logs',
        type=int,
        metavar='N',
        help='View last N login attempts instead of performing login'
    )
    parser.add_argument(
        '--max-attempts',
        type=int,
        default=5,
        help='Maximum number of login attempts to show when viewing logs (default: 5)'
    )

    return parser.parse_args()


def clear_logs():
    """Deletes all logs from the login_attempts table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM login_attempts")
    conn.commit()
    conn.close()
    print("✅ All logs have been cleared.")

def test_connection(network_name=None):
    """Tests if the login URL is reachable."""
    try:
        if MULTI_NETWORK_SUPPORT:
            manager = NetworkProfileManager()
            network_profile_name, network_config = manager.get_network_profile(network_name, auto_detect=True)
            url = network_config["wifi_url"]
            print(f"🔗 Testing connection for network '{network_profile_name}' to {url}...")
        else:
            config = load_config()
            url = config["wifi_url"]
            print(f"🔗 Testing connection to {url}...")
        
        response = requests.head(url, timeout=5) # Use HEAD to be efficient
        if response.status_code == 200:
            print(f"✅ Connection successful! The server responded with status {response.status_code}.")
        else:
            print(f"⚠️ Connection successful, but the server responded with status {response.status_code}.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")

def run_setup_wizard():
    """Guides the user through an interactive setup process."""
    print("--- WiFi-Auto-Auth Interactive Setup ---")
    print("This wizard will help you configure the script.")
    print()
    
    # Ask about multi-network setup
    print("Choose configuration type:")
    print("1. Single Network (Legacy)")
    print("2. Multi-Network (Recommended)")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == "2":
        setup_multi_network()
    else:
        setup_single_network()

def setup_single_network():
    """Set up single network configuration."""
    print("\n--- Single Network Setup ---")
    
    url = input("1. Enter the POST request URL from your network's login page: ")
    username = input("2. Enter your login username: ")
    password = input("3. Enter your login password: ")
    product_type = input("4. Enter product type (optional, press Enter for default): ") or "0"
    
    config = {
        "wifi_url": url,
        "username": username,
        "password": password,
        "product_type": product_type,
        "dashboard": {
            "host": "127.0.0.1",
            "port": 8000,
            "username": "admin",
            "password": "admin123"
        }
    }
    
    save_config(config)
    print("\n✅ Single network setup complete!")

def setup_multi_network():
    """Set up multi-network configuration."""
    print("\n--- Multi-Network Setup ---")
    
    networks = {}
    default_network = None
    
    while True:
        print(f"\n--- Network Profile #{len(networks) + 1} ---")
        
        profile_name = input("Enter network profile name (e.g., home, work, school): ").strip()
        if not profile_name:
            break
            
        ssid = input(f"Enter SSID for {profile_name}: ").strip()
        url = input(f"Enter login URL for {profile_name}: ").strip()
        username = input(f"Enter username for {profile_name}: ").strip()
        password = input(f"Enter password for {profile_name}: ").strip()
        product_type = input(f"Enter product type for {profile_name} (optional): ").strip() or "0"
        description = input(f"Enter description for {profile_name} (optional): ").strip() or f"{profile_name.title()} network"
        
        networks[profile_name] = {
            "ssid": ssid,
            "wifi_url": url,
            "username": username,
            "password": password,
            "product_type": product_type,
            "description": description
        }
        
        if not default_network:
            default_network = profile_name
        
        add_more = input(f"\nAdd another network profile? (y/N): ").strip().lower()
        if add_more not in ['y', 'yes']:
            break
    
    if not networks:
        print("No networks configured. Falling back to single network setup.")
        setup_single_network()
        return
    
    # Ask for default network
    if len(networks) > 1:
        print(f"\nAvailable networks: {', '.join(networks.keys())}")
        default_choice = input(f"Enter default network (press Enter for '{default_network}'): ").strip()
        if default_choice in networks:
            default_network = default_choice
    
    config = {
        "default_network": default_network,
        "networks": networks,
        "dashboard": {
            "host": "127.0.0.1",
            "port": 8000,
            "username": "admin",
            "password": "admin123"
        }
    }
    
    save_config(config)
    print(f"\n✅ Multi-network setup complete! {len(networks)} networks configured.")
    print(f"Default network: {default_network}")

def save_config(config):
    """Save configuration to config.json file."""
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\n💾 Configuration saved to {CONFIG_PATH}")
    except Exception as e:
        print(f"\n❌ Error saving configuration: {e}")

def list_networks():
    """List all configured network profiles."""
    if not MULTI_NETWORK_SUPPORT:
        print("❌ Multi-network support not available. Using legacy configuration.")
        return
    
    try:
        manager = NetworkProfileManager()
        networks = manager.list_networks()
        current_ssid = get_current_ssid()
        
        print("\n📶 Configured Network Profiles:")
        print("=" * 60)
        
        for name, config in networks.items():
            ssid = config.get("ssid", "Unknown")
            url = config.get("wifi_url", "Unknown")
            description = config.get("description", "No description")
            
            # Mark current network
            current_marker = " 📍 CURRENT" if ssid == current_ssid else ""
            
            print(f"🌐 Network: {name}{current_marker}")
            print(f"   SSID: {ssid}")
            print(f"   URL: {url}")
            print(f"   Description: {description}")
            print("-" * 60)
            
        if current_ssid:
            print(f"\n📡 Currently connected to: {current_ssid}")
        else:
            print("\n📡 No WiFi connection detected")
            
    except Exception as e:
        print(f"❌ Error listing networks: {e}")

def detect_network():
    """Detect current network and show matching profile."""
    if not MULTI_NETWORK_SUPPORT:
        print("❌ Multi-network support not available.")
        return
    
    try:
        current_ssid = get_current_ssid()
        
        if not current_ssid:
            print("📡 No WiFi connection detected")
            return
        
        print(f"📡 Current SSID: {current_ssid}")
        
        manager = NetworkProfileManager()
        try:
            network_name, network_config = manager.get_network_profile(auto_detect=True)
            print(f"✅ Found matching profile: {network_name}")
            print(f"   Description: {network_config.get('description', 'No description')}")
            print(f"   Login URL: {network_config.get('wifi_url', 'Unknown')}")
        except Exception:
            print("⚠️ No matching network profile found")
            print("💡 You may need to add this network to your config.json")
            
    except Exception as e:
        print(f"❌ Error detecting network: {e}")

def start_dashboard():
    """Start the web dashboard server."""
    try:
        import subprocess
        import sys
        print("🚀 Starting WiFi Auto Auth Dashboard...")
        print("📊 Dashboard will be available at: http://127.0.0.1:8000")
        print("🔑 Default credentials: admin / admin123")
        print("🛑 Press Ctrl+C to stop the server")
        
        # Start the dashboard server
        subprocess.run([sys.executable, "dashboard.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting dashboard: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Dashboard server stopped.")
    except ImportError:
        print("❌ Dashboard dependencies not installed. Please run: pip install -r requirements.txt")
    except FileNotFoundError:
        print("❌ Dashboard server not found. Please ensure dashboard.py exists.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script to automatically log into captive portal WiFi networks with multi-network support."
    )
    
    parser.add_argument(
        '--login', 
        action='store_true', 
        help="Perform a login attempt."
    )
    parser.add_argument(
        '--network', '-n',
        type=str,
        metavar='PROFILE',
        help="Specify which network profile to use (overrides auto-detection)."
    )
    parser.add_argument(
        '--view-logs', 
        nargs='?', 
        const=5, 
        type=int, 
        metavar='N', 
        help="View the last N login attempts. Defaults to 5 if no number is provided."
    )
    parser.add_argument(
        '--network-filter',
        type=str,
        metavar='PROFILE',
        help="Filter logs by network profile name."
    )
    parser.add_argument(
        '--list-networks',
        action='store_true',
        help="List all configured network profiles."
    )
    parser.add_argument(
        '--detect-network',
        action='store_true',
        help="Detect current network and show matching profile."
    )
    parser.add_argument(
        '--setup', 
        action='store_true', 
        help="Run the interactive setup wizard to configure credentials."
    )
    parser.add_argument(
        '--test', 
        action='store_true', 
        help="Test the connection to the login URL without logging in."
    )
    parser.add_argument(
        '--clear-logs', 
        action='store_true', 
        help="Clear all login logs from the database."
    )
    parser.add_argument(
        '--dashboard', 
        action='store_true', 
        help="Start the web dashboard server for monitoring login attempts."
    )

    args = parser.parse_args()
    
    # For operations that don't need config, handle them first
    if args.setup:
        run_setup_wizard()
    elif args.dashboard:
        start_dashboard()
    elif args.list_networks:
        list_networks()
    elif args.detect_network:
        detect_network()
    else:
        # For operations that need database/config
        try:
            setup_database()  # Ensure the database is always set up
            
            if args.login:
                wifi_login(args.network)
            elif args.view_logs is not None:
                view_logs(args.view_logs, args.network_filter)
            elif args.test:
                test_connection(args.network)
            elif args.clear_logs:
                clear_logs()
            else:
                print("No arguments provided. Performing default login action.")
                wifi_login(args.network)
                view_logs(1, args.network_filter)
                
        except FileNotFoundError as e:
            print(f"❌ Configuration Error: {e}")
            print("💡 Run 'python wifi_auto_login.py --setup' to configure the application.")
            print("📖 Or copy config.example.json to config.json and edit it manually.")
