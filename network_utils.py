"""
Network utilities for WiFi Auto Auth - Multi-Network Support
Handles network detection, SSID identification, and network profile management.
"""

import subprocess
import platform
import re
import json
import os
from typing import Optional, Dict, List, Tuple
from config.logging_config import get_logger

logger = get_logger(__name__)

class NetworkDetector:
    """Handles network detection and SSID identification across different platforms."""
    
    def __init__(self):
        self.platform = platform.system().lower()
        logger.debug(f"Initialized NetworkDetector for platform: {self.platform}")
    
    def get_current_ssid(self) -> Optional[str]:
        """
        Get the SSID of the currently connected WiFi network.
        
        Returns:
            str: SSID of current network, or None if not connected to WiFi
        """
        try:
            if self.platform == "windows":
                return self._get_ssid_windows()
            elif self.platform == "darwin":  # macOS
                return self._get_ssid_macos()
            elif self.platform == "linux":
                return self._get_ssid_linux()
            else:
                logger.warning(f"Unsupported platform: {self.platform}")
                return None
        except Exception as e:
            logger.error(f"Failed to get current SSID: {e}")
            return None
    
    def _get_ssid_windows(self) -> Optional[str]:
        """Get SSID on Windows using netsh command."""
        try:
            # Use netsh to get WiFi profile information
            cmd = ["netsh", "wlan", "show", "profiles"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Get the currently connected profile
            cmd_interfaces = ["netsh", "wlan", "show", "interfaces"]
            interfaces_result = subprocess.run(cmd_interfaces, capture_output=True, text=True, check=True)
            
            # Parse the SSID from the interfaces output
            for line in interfaces_result.stdout.split('\n'):
                if 'SSID' in line and 'BSSID' not in line:
                    # Extract SSID (format: "    SSID                   : NetworkName")
                    match = re.search(r'SSID\s*:\s*(.+)', line.strip())
                    if match:
                        ssid = match.group(1).strip()
                        logger.debug(f"Detected Windows SSID: {ssid}")
                        return ssid
            
            logger.debug("No active WiFi connection found on Windows")
            return None
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Windows netsh command failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting Windows SSID: {e}")
            return None
    
    def _get_ssid_macos(self) -> Optional[str]:
        """Get SSID on macOS using airport utility."""
        try:
            # Try using networksetup first
            cmd = ["networksetup", "-getairportnetwork", "en0"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse output (format: "Current Wi-Fi Network: NetworkName")
            if "Current Wi-Fi Network:" in result.stdout:
                ssid = result.stdout.split("Current Wi-Fi Network:")[-1].strip()
                if ssid and ssid != "You are not associated with an AirPort network.":
                    logger.debug(f"Detected macOS SSID: {ssid}")
                    return ssid
            
            # Fallback to airport utility
            airport_cmd = ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"]
            airport_result = subprocess.run(airport_cmd, capture_output=True, text=True, check=True)
            
            for line in airport_result.stdout.split('\n'):
                if 'SSID:' in line:
                    ssid = line.split('SSID:')[-1].strip()
                    logger.debug(f"Detected macOS SSID via airport: {ssid}")
                    return ssid
            
            logger.debug("No active WiFi connection found on macOS")
            return None
            
        except subprocess.CalledProcessError as e:
            logger.error(f"macOS network command failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting macOS SSID: {e}")
            return None
    
    def _get_ssid_linux(self) -> Optional[str]:
        """Get SSID on Linux using various methods."""
        methods = [
            self._linux_iwgetid,
            self._linux_nmcli,
            self._linux_iwconfig
        ]
        
        for method in methods:
            try:
                ssid = method()
                if ssid:
                    logger.debug(f"Detected Linux SSID: {ssid}")
                    return ssid
            except Exception as e:
                logger.debug(f"Linux method {method.__name__} failed: {e}")
                continue
        
        logger.debug("No active WiFi connection found on Linux")
        return None
    
    def _linux_iwgetid(self) -> Optional[str]:
        """Get SSID using iwgetid command."""
        cmd = ["iwgetid", "-r"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        ssid = result.stdout.strip()
        return ssid if ssid else None
    
    def _linux_nmcli(self) -> Optional[str]:
        """Get SSID using NetworkManager's nmcli."""
        cmd = ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        for line in result.stdout.split('\n'):
            if line.startswith('yes:'):
                ssid = line.split(':', 1)[1]
                return ssid if ssid else None
        return None
    
    def _linux_iwconfig(self) -> Optional[str]:
        """Get SSID using iwconfig command."""
        cmd = ["iwconfig"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        for line in result.stdout.split('\n'):
            if 'ESSID:' in line:
                match = re.search(r'ESSID:"([^"]*)"', line)
                if match:
                    return match.group(1)
        return None


class NetworkProfileManager:
    """Manages network profiles and configuration loading."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.detector = NetworkDetector()
        logger.debug(f"Initialized NetworkProfileManager with config: {config_path}")
    
    def load_config(self) -> Dict:
        """Load and parse configuration file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Missing {self.config_path}. Please copy config.example.json to {self.config_path} and configure your networks."
            )
        
        with open(self.config_path, "r") as f:
            config = json.load(f)
        
        logger.debug(f"Loaded configuration from {self.config_path}")
        return config
    
    def get_available_networks(self) -> List[str]:
        """Get list of configured network profile names."""
        try:
            config = self.load_config()
            
            # Handle both new multi-network format and legacy format
            if "networks" in config:
                networks = list(config["networks"].keys())
                logger.debug(f"Found configured networks: {networks}")
                return networks
            else:
                # Legacy single network configuration
                logger.debug("Using legacy single network configuration")
                return ["default"]
        except Exception as e:
            logger.error(f"Error getting available networks: {e}")
            return []
    
    def get_network_profile(self, network_name: Optional[str] = None, auto_detect: bool = True) -> Tuple[str, Dict]:
        """
        Get network configuration for specified network or auto-detect current network.
        
        Args:
            network_name: Specific network profile to use
            auto_detect: Whether to auto-detect current network if network_name is None
            
        Returns:
            Tuple of (network_name, network_config)
        """
        config = self.load_config()
        
        # Handle legacy configuration format
        if "networks" not in config:
            logger.info("Using legacy configuration format")
            legacy_config = {
                "ssid": config.get("ssid", "Unknown"),
                "wifi_url": config["wifi_url"],
                "username": config["username"],
                "password": config["password"],
                "product_type": config.get("product_type", "0"),
                "description": "Legacy configuration"
            }
            return "legacy", legacy_config
        
        networks = config["networks"]
        
        # If specific network requested, use it
        if network_name:
            if network_name in networks:
                logger.info(f"Using specified network profile: {network_name}")
                return network_name, networks[network_name]
            else:
                raise ValueError(f"Network profile '{network_name}' not found in configuration")
        
        # Auto-detect current network
        if auto_detect:
            current_ssid = self.detector.get_current_ssid()
            if current_ssid:
                logger.info(f"Detected current SSID: {current_ssid}")
                
                # Find matching network profile by SSID
                for profile_name, profile_config in networks.items():
                    if profile_config.get("ssid") == current_ssid:
                        logger.info(f"Found matching network profile: {profile_name}")
                        return profile_name, profile_config
                
                logger.warning(f"No network profile found for SSID: {current_ssid}")
            else:
                logger.warning("Could not detect current network SSID")
        
        # Fall back to default network
        default_network = config.get("default_network", list(networks.keys())[0])
        if default_network in networks:
            logger.info(f"Using default network profile: {default_network}")
            return default_network, networks[default_network]
        
        # If default not found, use first available
        first_network = list(networks.keys())[0]
        logger.info(f"Using first available network profile: {first_network}")
        return first_network, networks[first_network]
    
    def list_networks(self) -> Dict[str, Dict]:
        """Get detailed information about all configured networks."""
        try:
            config = self.load_config()
            
            if "networks" not in config:
                # Legacy format
                return {
                    "legacy": {
                        "ssid": config.get("ssid", "Unknown"),
                        "wifi_url": config["wifi_url"],
                        "description": "Legacy configuration"
                    }
                }
            
            return config["networks"]
        except Exception as e:
            logger.error(f"Error listing networks: {e}")
            return {}


# Convenience functions for backward compatibility
def get_current_ssid() -> Optional[str]:
    """Get the SSID of the currently connected WiFi network."""
    detector = NetworkDetector()
    return detector.get_current_ssid()


def get_network_profile(network_name: Optional[str] = None, auto_detect: bool = True) -> Tuple[str, Dict]:
    """Get network configuration for specified network or auto-detect current network."""
    manager = NetworkProfileManager()
    return manager.get_network_profile(network_name, auto_detect)


def list_available_networks() -> List[str]:
    """Get list of configured network profile names."""
    manager = NetworkProfileManager()
    return manager.get_available_networks()