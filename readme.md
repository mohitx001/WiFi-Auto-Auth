# **WiFi-Auto-Auth**
Tired of entering the same Wi-Fi credentials every time you join the network? So was I! At my institute, logging into Wi-Fi manually was a hassle, so I built this Auto WiFi Login Script to automate the process with the help of Python,SQLite and Crontab!

This script automatically logs into Wi-Fi networks using pre-saved credentials and now comes with SQLite integration to store login attempts and all payload parameters. It keeps track of all login activities, captures dynamic session parameters (a), and provides a user-friendly log display for debugging.

Ideal for schools, workplaces, or any location with recurring Wi-Fi logins, this script eliminates manual re-authentication and ensures effortless connectivity. It's fully customizable, works across different networks, and can even be automated on startup for a seamless experience.

## **🚀 New: Web Dashboard**

**Beautiful web-based monitoring interface with real-time statistics and interactive charts!**

### **Dashboard Features**
- 📊 Real-time statistics & success rates
- 📈 Interactive time-based visualizations  
- 🔍 Advanced filtering & search
- 📱 Mobile-responsive design
- 🔒 Secure authentication
- ⚡ Auto-refresh every 30 seconds

### **Quick Start**
```bash
# Install dependencies
pip install -r requirements.txt

# Start dashboard
python wifi_auto_login.py --dashboard

# Access: http://127.0.0.1:8000 (admin/admin123)
```

**📖 Full documentation: [DASHBOARD.md](DASHBOARD.md)**

## **🌐 NEW: Multi-Network Support**

**Automatically handle multiple WiFi networks with intelligent auto-detection!**

### **Multi-Network Features**
- 🏠 **Multiple Profiles**: Configure home, work, school networks
- 🔍 **Auto-Detection**: Automatically detects current SSID
- 📱 **Smart Selection**: Chooses appropriate credentials
- 📊 **Network Analytics**: Per-network statistics in dashboard
- 🔄 **Seamless Switching**: No manual intervention needed
- 📋 **Easy Management**: List, detect, and filter by network

### **Quick Multi-Network Setup**
```bash
# Copy and configure multi-network template
cp config.example.json config.json

# List configured networks
python wifi_auto_login.py --list-networks

# Auto-detect current network
python wifi_auto_login.py --detect-network

# Login with auto-detection
python wifi_auto_login.py --login

# Use specific network profile
python wifi_auto_login.py --login --network work
```

**📖 Complete guide: [MULTI_NETWORK.md](MULTI_NETWORK.md)**

## **Logging Options**

This application features a comprehensive professional logging system that provides detailed insights into login attempts, debugging information, and system status. The logging system supports multiple output destinations, configurable log levels, and automatic log rotation.

### **Command Line Arguments**

The script accepts various logging-related command line arguments:

- `--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}`: Set the logging level (default: INFO)
- `--log-file` / `--no-log-file`: Enable or disable file logging (default: enabled)
- `--log-dir DIR`: Directory for log files (default: ./logs)
- `--console-logging` / `--no-console-logging`: Enable or disable console logging (default: enabled)
- `--view-logs N`: View last N login attempts instead of performing login
- `--max-attempts N`: Maximum number of login attempts to show (default: 5)

**Usage Examples:**

```bash
# Run with debug logging
python wifi_auto_login.py --log-level DEBUG

# View recent login attempts
python wifi_auto_login.py --view-logs 10

# Start the web dashboard
python wifi_auto_login.py --dashboard

# Disable file logging, only console output
python wifi_auto_login.py --no-log-file

# Custom log directory
python wifi_auto_login.py --log-dir /var/log/wifi-auth
```

### **Environment Variables**

Configure logging behavior using environment variables:

- `LOG_LEVEL`: Overall logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `CONSOLE_LOG_LEVEL`: Separate level for console output
- `CONSOLE_LOGGING_ENABLED`: Enable/disable console logging (true/false)
- `LOG_FILE_ENABLED`: Enable/disable file logging (true/false)
- `LOG_DIR`: Directory for log files (default: ./logs)
- `LOG_MAX_BYTES`: Maximum log file size before rotation (default: 10485760 = 10MB)
- `LOG_BACKUP_COUNT`: Number of backup log files to keep (default: 5)

**Example:**

```bash
export LOG_LEVEL=DEBUG
export LOG_DIR=/home/user/logs
python wifi_auto_login.py
```

### **Log Rotation**

The application automatically rotates log files when they reach the maximum size (default 10MB). It keeps up to 5 backup files, ensuring logs don't consume excessive disk space while maintaining historical data.

Log files are stored in the configured log directory with the name `wifi_auto_auth.log`, and rotated files are named `wifi_auto_auth.log.1`, `wifi_auto_auth.log.2`, etc.

### **For step-by-step setup instructions, please refer to [setup.md](https://github.com/01bps/WiFi-Auto-Auth/blob/main/setup.md)**

## **Security Notes**
- Credentials are securely stored in an SQLite database within your home directory.
- No sensitive data is transmitted except during the login request.
- Passwords are masked in logs for security.
- Login attempts are logged in SQLite, and old logs are automatically deleted after reboot


# **License:**
   This project is licensed under the [MIT License](LICENSE), which allows for free use, modification, and distribution.

🔧 **Need help?** Open an issue on GitHub!
