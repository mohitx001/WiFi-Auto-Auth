# Multi-Network Support Guide

WiFi Auto Auth now supports multiple network profiles, allowing you to automatically connect to different WiFi networks (home, work, school, etc.) with different credentials and settings.

## Features

- **Auto-Detection**: Automatically detects current network SSID and selects appropriate profile
- **Manual Selection**: Override auto-detection by specifying a network profile
- **Network-Specific Logging**: Track login attempts per network
- **Dashboard Integration**: View network-specific statistics in the web dashboard
- **Backward Compatibility**: Existing single-network configurations continue to work

## Configuration

### New Multi-Network Format

Create or update your `config.json` file with the new multi-network format:

```json
{
  "default_network": "home",
  "networks": {
    "home": {
      "ssid": "HomeWiFi",
      "wifi_url": "http://192.168.1.1/login",
      "username": "your_home_username",
      "password": "your_home_password",
      "product_type": "router",
      "description": "Home WiFi network"
    },
    "work": {
      "ssid": "OfficeWiFi",
      "wifi_url": "http://10.0.0.1/login",
      "username": "your_work_username",
      "password": "your_work_password",
      "product_type": "enterprise",
      "description": "Work WiFi network"
    },
    "school": {
      "ssid": "SchoolWiFi",
      "wifi_url": "http://172.16.1.1/login",
      "username": "your_school_username",
      "password": "your_school_password",
      "product_type": "edu",
      "description": "School WiFi network"
    }
  },
  "dashboard": {
    "host": "127.0.0.1",
    "port": 8000,
    "username": "admin",
    "password": "admin123"
  }
}
```

### Legacy Configuration Support

Existing single-network configurations will continue to work:

```json
{
  "wifi_url": "http://192.168.1.1/login",
  "username": "your_username",
  "password": "your_password",
  "product_type": "router"
}
```

## Usage

### Auto-Detection (Recommended)

The script automatically detects your current network SSID and selects the appropriate profile:

```bash
# Auto-detect current network and login
python wifi_auto_login.py --login

# Auto-detect and show recent logs
python wifi_auto_login.py
```

### Manual Network Selection

Override auto-detection by specifying a network profile:

```bash
# Login using specific network profile
python wifi_auto_login.py --login --network work

# Test connection for specific network
python wifi_auto_login.py --test --network home
```

### Network Management Commands

```bash
# List all configured network profiles
python wifi_auto_login.py --list-networks

# Detect current network and show matching profile
python wifi_auto_login.py --detect-network

# View logs for specific network
python wifi_auto_login.py --view-logs 10 --network-filter work
```

## Command Reference

### New Commands

| Command | Description |
|---------|-------------|
| `--network PROFILE` | Use specific network profile |
| `--list-networks` | List all configured networks |
| `--detect-network` | Detect current network |
| `--network-filter PROFILE` | Filter logs by network |

### Updated Commands

| Command | Description |
|---------|-------------|
| `--login` | Auto-detects network or uses --network |
| `--test` | Tests connection for detected/specified network |
| `--view-logs N` | Shows network info in logs |

## Network Detection

The script uses platform-specific methods to detect your current WiFi network:

### Windows
- Uses `netsh wlan show interfaces` command
- Requires WiFi adapter to be connected

### macOS  
- Uses `networksetup -getairportnetwork en0` command
- Falls back to `airport -I` utility

### Linux
- Tries multiple methods: `iwgetid`, `nmcli`, `iwconfig`
- Requires appropriate network utilities installed

## Database Schema

The database now includes network information:

```sql
CREATE TABLE login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    network_name TEXT,        -- New: Network profile name
    network_ssid TEXT,        -- New: Actual SSID
    username TEXT,
    password TEXT,
    a TEXT,
    response_status TEXT,
    response_message TEXT
);
```

Existing databases are automatically upgraded with new columns.

## Dashboard Features

### Network Statistics
- Per-network success rates
- Network-specific attempt counts
- Last login time per network

### Filtering
- Filter logs by network profile
- Network-specific historical data
- Multi-network overview

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/network-stats` | Get per-network statistics |
| `/api/attempts?network_filter=PROFILE` | Filtered login attempts |

## Migration Guide

### From Single Network to Multi-Network

1. **Backup your current config.json**:
   ```bash
   cp config.json config.json.backup
   ```

2. **Update configuration format**:
   ```bash
   # Use the new example as template
   cp config.example.json config.json
   # Edit config.json with your networks
   ```

3. **Test the configuration**:
   ```bash
   python wifi_auto_login.py --list-networks
   python wifi_auto_login.py --detect-network
   ```

### Gradual Migration

You can keep using legacy format while adding new networks:

```json
{
  "wifi_url": "http://192.168.1.1/login",
  "username": "legacy_user",
  "password": "legacy_pass",
  "networks": {
    "work": {
      "ssid": "OfficeWiFi",
      "wifi_url": "http://10.0.0.1/login",
      "username": "work_user",
      "password": "work_pass"
    }
  }
}
```

## Troubleshooting

### Network Detection Issues

1. **No SSID detected**:
   ```bash
   # Check if WiFi is connected
   python wifi_auto_login.py --detect-network
   
   # Manually specify network
   python wifi_auto_login.py --login --network home
   ```

2. **Platform not supported**:
   - Windows: Ensure you have admin privileges for netsh
   - macOS: Check if networksetup is available
   - Linux: Install wireless-tools or network-manager

3. **Profile not found**:
   ```bash
   # List available profiles
   python wifi_auto_login.py --list-networks
   
   # Check SSID matches exactly
   python wifi_auto_login.py --detect-network
   ```

### Configuration Issues

1. **Invalid JSON**:
   ```bash
   # Validate JSON syntax
   python -m json.tool config.json
   ```

2. **Missing network profile**:
   - Add the network to your config.json
   - Ensure SSID matches exactly (case-sensitive)

3. **Legacy compatibility**:
   - Old format still works
   - Gradually migrate to new format

## Best Practices

### Network Profile Design

1. **Use descriptive names**: `home`, `work`, `coffee-shop`
2. **Include descriptions**: Help identify networks later
3. **Set default network**: For fallback when detection fails
4. **Test each profile**: Verify credentials before deployment

### Security Considerations

1. **Protect config.json**: Contains passwords in plain text
2. **Use different passwords**: Don't reuse across networks
3. **Regular updates**: Change passwords periodically
4. **Backup configurations**: Keep secure backups

### Monitoring

1. **Use dashboard**: Monitor per-network success rates
2. **Check logs regularly**: Identify authentication issues
3. **Network-specific analysis**: Filter logs by network
4. **Set up alerts**: Monitor for failure patterns

## Examples

### Complete Multi-Network Setup

```bash
# 1. Set up configuration
cp config.example.json config.json
# Edit config.json with your networks

# 2. Test configuration
python wifi_auto_login.py --list-networks
python wifi_auto_login.py --detect-network

# 3. Test each network
python wifi_auto_login.py --test --network home
python wifi_auto_login.py --test --network work

# 4. Set up automatic login
python wifi_auto_login.py --login

# 5. Monitor via dashboard
python wifi_auto_login.py --dashboard
```

### Automated Network Switching

```bash
#!/bin/bash
# Example script for automated network handling

# Detect current network
CURRENT_NETWORK=$(python wifi_auto_login.py --detect-network 2>/dev/null | grep "Found matching profile" | cut -d: -f2 | xargs)

if [ -n "$CURRENT_NETWORK" ]; then
    echo "Logging into detected network: $CURRENT_NETWORK"
    python wifi_auto_login.py --login --network "$CURRENT_NETWORK"
else
    echo "No matching network profile found, using auto-detection"
    python wifi_auto_login.py --login
fi
```

## Support

If you encounter issues with multi-network support:

1. Check the troubleshooting section above
2. Enable debug logging: `python wifi_auto_login.py --log-level DEBUG`
3. Test with single network first
4. Report issues with network detection details
5. Include platform information (Windows/macOS/Linux)

The multi-network feature is designed to be backward compatible while providing powerful new capabilities for managing multiple WiFi environments.