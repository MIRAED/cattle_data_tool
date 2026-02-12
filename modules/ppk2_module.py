# -*- coding: utf-8 -*-
"""
PPK2 (Power Profiler Kit 2) Module
Wrapper for ppk2-api-python library (PPK2_MP multiprocessing version)
"""

import time
from enum import Enum, auto

try:
    from ppk2_api.ppk2_api import PPK2_MP
    import serial.tools.list_ports
    PPK2_AVAILABLE = True
except ImportError:
    PPK2_AVAILABLE = False
    print("ppk2-api-python not available. Install with: pip install ppk2-api-python")


class PPK2Mode(Enum):
    """PPK2 operating modes"""
    SOURCE_METER = auto()  # PPK2 provides power to DUT
    AMPERE_METER = auto()  # PPK2 measures current from external source


class PPK2SampleRate(Enum):
    """PPK2 sample rates (based on read interval)"""
    RATE_5000HZ = (0.0002, "5000 Hz (0.2ms)")  # 0.2ms read interval - 매우 빠름
    RATE_2000HZ = (0.0005, "2000 Hz (0.5ms)")  # 0.5ms read interval - 매우 빠름
    RATE_1000HZ = (0.001, "1000 Hz (1ms)")     # 1ms read interval
    RATE_500HZ = (0.002, "500 Hz (2ms)")       # 2ms read interval
    RATE_200HZ = (0.005, "200 Hz (5ms)")       # 5ms read interval
    RATE_100HZ = (0.01, "100 Hz (10ms)")       # 10ms read interval
    RATE_50HZ = (0.02, "50 Hz (20ms)")         # 20ms read interval
    RATE_10Hz = (0.1, "10 Hz (100ms)")         # 100ms read interval

    def __init__(self, interval, label):
        self.interval = interval
        self.label = label


class PPK2Manager:
    """Manager class for PPK2 device"""

    def __init__(self):
        self.ppk2 = None
        self.connected = False
        self.port = None
        self.mode = PPK2Mode.SOURCE_METER
        self.voltage_mv = 3300  # Default 3.3V
        self.dut_power_on = False
        self.measuring = False

    def scan_devices(self):
        """
        Scan for PPK2 devices on available COM ports
        Returns: list of (port, description) tuples
        """
        if not PPK2_AVAILABLE:
            return []

        try:
            # Manual scanning using serial.tools.list_ports
            # Note: PPK2_MP.list_devices() causes initialization errors, so we use manual scanning
            ppk2_devices = []
            ports = serial.tools.list_ports.comports()

            for port in ports:
                # PPK2 typically shows as "nRF Connect USB CDC ACM" or similar
                # Also check for VID/PID: Nordic Semiconductor VID=1915 PID=C00A
                desc_upper = port.description.upper()

                is_ppk2 = False

                # Check by description
                if 'PPK2' in desc_upper or \
                   'POWER PROFILER' in desc_upper:
                    is_ppk2 = True

                # Check by manufacturer/product
                elif 'NRF' in desc_upper or \
                     'NORDIC' in desc_upper:
                    # Additional check: Nordic devices with CDC ACM
                    if 'CDC' in desc_upper or 'ACM' in desc_upper:
                        is_ppk2 = True

                # Note: VID/PID check disabled (Nordic VID=0x1915, PID=0xC00A)
                # as description-based detection is more reliable

                if is_ppk2:
                    ppk2_devices.append((port.device, port.description))
                    print(f"Found PPK2 device: {port.device} - {port.description}")

            return ppk2_devices

        except Exception as ex:
            print(f"Error scanning for PPK2 devices: {ex}")
            import traceback
            traceback.print_exc()
            return []

    def connect(self, port):
        """
        Connect to PPK2 device
        Args:
            port: COM port string (e.g., 'COM3')
        Returns:
            True if successful, False otherwise
        """
        if not PPK2_AVAILABLE:
            print("PPK2 API not available")
            return False

        try:
            if self.connected:
                self.disconnect()

            print(f"Attempting to connect to PPK2 on {port}...")

            # Initialize PPK2_MP with optimized buffer settings
            # PPK2 samples at 100kHz internally, so we need appropriate chunk size
            # buffer_chunk_seconds determines how often the background process reads from serial
            # Too small values cause overhead, too large values cause latency
            # Optimal: 0.01s (10ms) - reads 1000 samples per chunk at 100kHz
            self.ppk2 = PPK2_MP(
                port,
                buffer_max_size_seconds=10,      # Max buffer: 10 seconds
                buffer_chunk_seconds=0.01,       # Read chunk: 10ms (1000 samples @ 100kHz)
                timeout=1,                       # Serial read timeout
                write_timeout=1,                 # Serial write timeout
                exclusive=True                   # Exclusive port access
            )
            self.port = port

            # Wait for device to initialize
            import time
            time.sleep(0.5)

            # Try to reset the device first to clear any bad state
            try:
                if hasattr(self.ppk2, 'ser') and self.ppk2.ser:
                    # Clear input/output buffers
                    self.ppk2.ser.reset_input_buffer()
                    self.ppk2.ser.reset_output_buffer()
                    print("PPK2 serial buffers cleared")
                    time.sleep(0.2)
            except Exception as ex:
                print(f"Warning: Could not clear serial buffers: {ex}")

            # Get device modifiers (required initialization step)
            # Retry a few times if it fails due to decoding errors
            max_retries = 3
            modifiers = None
            for retry in range(max_retries):
                try:
                    modifiers = self.ppk2.get_modifiers()
                    print(f"PPK2 connected on {port}")
                    print(f"Modifiers: {modifiers}")
                    break
                except UnicodeDecodeError as ex:
                    if retry < max_retries - 1:
                        print(f"Retry {retry + 1}/{max_retries}: UTF-8 decode error, retrying...")
                        # Clear buffers again
                        if hasattr(self.ppk2, 'ser') and self.ppk2.ser:
                            self.ppk2.ser.reset_input_buffer()
                            self.ppk2.ser.reset_output_buffer()
                        time.sleep(0.5)
                    else:
                        raise

            self.connected = True
            return True

        except PermissionError as ex:
            print(f"Failed to connect to PPK2 on {port}: Permission denied")
            print(f"  → Port may be in use by another application")
            print(f"  → Close nRF Connect, Power Profiler, or other serial programs")
            print(f"  → Or try running as Administrator")
            print(f"  Error details: {ex}")
            # Clean up partial initialization
            if self.ppk2:
                try:
                    if hasattr(self.ppk2, 'stop'):
                        self.ppk2.stop()
                except:
                    pass
                self.ppk2 = None
            self.connected = False
            return False
        except Exception as ex:
            print(f"Failed to connect to PPK2 on {port}: {ex}")
            import traceback
            traceback.print_exc()
            # Clean up partial initialization
            if self.ppk2:
                try:
                    if hasattr(self.ppk2, 'stop'):
                        self.ppk2.stop()
                except:
                    pass
                self.ppk2 = None
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from PPK2 device"""
        try:
            if self.measuring:
                self.stop_measurement()

            if self.ppk2:
                # Turn off DUT power before disconnecting (always, for safety)
                try:
                    if hasattr(self.ppk2, 'toggle_DUT_power'):
                        self.ppk2.toggle_DUT_power("OFF")
                        self.dut_power_on = False
                except:
                    # Ignore any errors during power off
                    pass

                # Properly close PPK2_MP and its background process
                try:
                    # PPK2_MP has a stop() method to clean up the background process
                    if hasattr(self.ppk2, 'stop'):
                        self.ppk2.stop()
                        print("PPK2_MP background process stopped")

                    # Close the serial port if available
                    if hasattr(self.ppk2, 'ser') and self.ppk2.ser:
                        if hasattr(self.ppk2.ser, 'close'):
                            self.ppk2.ser.close()
                            print("PPK2 serial port closed")

                    # Give the port time to release
                    import time
                    time.sleep(0.5)

                except Exception as ex:
                    print(f"Error closing PPK2 resources: {ex}")

                # Clear reference
                self.ppk2 = None

            self.connected = False
            self.port = None
            print("PPK2 disconnected")
            return True

        except Exception as ex:
            print(f"Error disconnecting PPK2: {ex}")
            import traceback
            traceback.print_exc()
            return False

    def set_mode(self, mode):
        """
        Set PPK2 operating mode
        Args:
            mode: PPK2Mode.SOURCE_METER or PPK2Mode.AMPERE_METER
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("PPK2 not connected")
            return False

        try:
            if mode == PPK2Mode.SOURCE_METER:
                self.ppk2.use_source_meter()
                print("PPK2 mode: Source Meter")
            elif mode == PPK2Mode.AMPERE_METER:
                self.ppk2.use_ampere_meter()
                print("PPK2 mode: Ampere Meter")
            else:
                print(f"Invalid mode: {mode}")
                return False

            self.mode = mode
            return True

        except Exception as ex:
            print(f"Failed to set PPK2 mode: {ex}")
            return False

    def set_voltage(self, voltage_v):
        """
        Set source voltage (only in Source Meter mode)
        Args:
            voltage_v: Voltage in volts (0.0 - 5.0)
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("PPK2 not connected")
            return False

        if self.mode != PPK2Mode.SOURCE_METER:
            print("Voltage control only available in Source Meter mode")
            return False

        try:
            # Convert to millivolts (PPK2 API uses mV)
            voltage_mv = int(voltage_v * 1000)

            # Clamp to valid range (0-5000 mV)
            voltage_mv = max(0, min(5000, voltage_mv))

            self.ppk2.set_source_voltage(voltage_mv)
            self.voltage_mv = voltage_mv
            print(f"PPK2 voltage set to {voltage_mv} mV ({voltage_v:.3f} V)")
            return True

        except Exception as ex:
            print(f"Failed to set PPK2 voltage: {ex}")
            return False

    def toggle_dut_power(self, on):
        """
        Toggle DUT power on/off (only in Source Meter mode)
        Args:
            on: True to turn on, False to turn off
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("PPK2 not connected")
            return False

        if self.mode != PPK2Mode.SOURCE_METER:
            print("DUT power control only available in Source Meter mode")
            return False

        try:
            if on:
                self.ppk2.toggle_DUT_power("ON")
                print("PPK2 DUT power: ON")
            else:
                self.ppk2.toggle_DUT_power("OFF")
                print("PPK2 DUT power: OFF")

            self.dut_power_on = on
            return True

        except Exception as ex:
            print(f"Failed to toggle PPK2 DUT power: {ex}")
            return False

    def toggle_passthrough(self, on):
        """
        Toggle passthrough on/off (for Ampere Meter mode)
        In Ampere Meter mode, passthrough allows external power to reach DUT
        Args:
            on: True to turn on, False to turn off
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("PPK2 not connected")
            return False

        try:
            # In Ampere Meter mode, toggle_DUT_power acts as passthrough control
            if on:
                self.ppk2.toggle_DUT_power("ON")
                print("PPK2 Passthrough: ON")
            else:
                self.ppk2.toggle_DUT_power("OFF")
                print("PPK2 Passthrough: OFF")

            self.dut_power_on = on
            return True

        except Exception as ex:
            print(f"Failed to toggle PPK2 passthrough: {ex}")
            return False

    def start_measurement(self):
        """
        Start current measurement
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("PPK2 not connected")
            return False

        try:
            # PPK2 API requires voltage setting before start_measuring()
            # even in Ampere Meter mode (for API initialization)
            if self.mode == PPK2Mode.SOURCE_METER:
                # Source Meter: Set actual output voltage
                if self.voltage_mv == 0:
                    print("PPK2: Voltage not set, using default 3.3V")
                    self.set_voltage(3.3)
                else:
                    print(f"PPK2: Re-applying voltage setting: {self.voltage_mv}mV")
                    self.ppk2.set_source_voltage(self.voltage_mv)
            else:
                # Ampere Meter: Set dummy voltage for API (not actually output)
                if self.voltage_mv == 0:
                    self.voltage_mv = 3300  # Default 3.3V
                print(f"PPK2: Setting voltage for API initialization: {self.voltage_mv}mV")
                self.ppk2.set_source_voltage(self.voltage_mv)

            self.ppk2.start_measuring()
            self.measuring = True
            print("PPK2 measurement started")
            return True

        except Exception as ex:
            print(f"Failed to start PPK2 measurement: {ex}")
            import traceback
            traceback.print_exc()
            return False

    def stop_measurement(self):
        """
        Stop current measurement
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            return False

        try:
            if self.measuring:
                self.ppk2.stop_measuring()
                self.measuring = False
                print("PPK2 measurement stopped")
            return True

        except Exception as ex:
            print(f"Failed to stop PPK2 measurement: {ex}")
            return False

    def get_data(self):
        """
        Get measurement data from PPK2
        Returns:
            Numpy array of current values in microamps, or None if error
        """
        if not self.connected or not self.measuring:
            # Silently return None if not connected or measuring
            return None

        try:
            import numpy as np

            # get_data() returns raw bytes from PPK2 device
            read_data = self.ppk2.get_data()

            # Empty bytes means no new data available
            if read_data == b'':
                return None

            if read_data is not None and len(read_data) > 0:
                # Use get_samples() to convert raw bytes to current values in microamps
                # This is the official PPK2 API way to interpret the data
                samples = self.ppk2.get_samples(read_data)

                if samples and len(samples) > 0:
                    # samples는 이미 1D list 또는 numpy array
                    # asarray + flatten으로 확실하게 1D float64 배열로 만듦
                    data = np.asarray(samples, dtype=np.float64).flatten()
                    return data
                else:
                    return None
            else:
                return None

        except Exception as ex:
            print(f"PPK2 get_data error: {ex}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_available_sample_rates():
        """
        Get list of available sample rate labels
        Returns:
            List of sample rate label strings
        """
        return [rate.label for rate in PPK2SampleRate]

    @staticmethod
    def get_sample_rate_interval(rate_label):
        """
        Get read interval for a sample rate label
        Args:
            rate_label: Sample rate label string
        Returns:
            Read interval in seconds
        """
        for rate in PPK2SampleRate:
            if rate.label == rate_label:
                return rate.interval
        return 0.01  # Default to 10ms


# Module-level functions for compatibility with A344xxx module pattern
def scan_devices():
    """Scan for PPK2 devices (module-level function)"""
    manager = PPK2Manager()
    return manager.scan_devices()


if __name__ == "__main__":
    # Test code
    print("PPK2 Module Test")
    print(f"PPK2 API Available: {PPK2_AVAILABLE}")

    if PPK2_AVAILABLE:
        manager = PPK2Manager()

        print("\nScanning for PPK2 devices...")
        devices = manager.scan_devices()
        print(f"Found {len(devices)} device(s):")
        for port, desc in devices:
            print(f"  {port}: {desc}")

        print("\nAvailable sample rates:")
        for rate in PPK2Manager.get_available_sample_rates():
            print(f"  {rate}")
