#!/usr/bin/env python3

"""
A *really* simple rtl-tcp client, that manages basic operations and configuration.
Gist: https://gist.github.com/douxxtech/793fe37022d9551df3114f6d72498b94
"""

import numpy as np
import socket
import struct

class RTLTCPClient:
    """Simple RTL-TCP client for receiving IQ samples"""
    
    SET_FREQ = 0x01
    SET_SAMPLE_RATE = 0x02
    SET_GAIN_MODE = 0x03
    SET_GAIN = 0x04
    SET_FREQ_CORRECTION = 0x05
    
    def __init__(self, host='127.0.0.1', port=1234):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        
    def connect(self):
        """Connect to RTL-TCP server"""
        if self.connected: 
            self.disconnect()
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.host, self.port))
            self.connected = True
            return True
        except Exception:
            return False
    
    def disconnect(self):
        """Disconnect from server"""
        if self.socket:
            self.socket.close()
            self.connected = False
    
    def _send_command(self, cmd, value):
        """Send command to RTL-TCP server"""
        if not self.connected:
            return False
        try:
            if cmd == self.SET_FREQ_CORRECTION:
                data = struct.pack('>Bi', cmd, int(value))
            else:
                data = struct.pack('>BI', cmd, int(value))
            self.socket.send(data)
            return True
        except Exception:
            return False
    
    def set_frequency(self, freq_hz):
        """Set center frequency in Hz"""
        return self._send_command(self.SET_FREQ, int(freq_hz))
    
    def set_sample_rate(self, rate_hz):
        """Set sample rate in Hz"""
        return self._send_command(self.SET_SAMPLE_RATE, int(rate_hz))
    
    def set_gain_mode(self, manual=True):
        """Set gain mode (manual=True for manual, False for AGC)"""
        return self._send_command(self.SET_GAIN_MODE, 1 if manual else 0)
    
    def set_gain(self, gain_db):
        """Set gain in dB (tenths of dB, so 49.6 for max)"""
        return self._send_command(self.SET_GAIN, int(gain_db * 10))
    
    def set_freq_correction(self, ppm):
        """Set frequency correction in PPM"""
        return self._send_command(self.SET_FREQ_CORRECTION, int(ppm))
    
    def read_samples(self, num_samples):
        """
        Read IQ samples from RTL-TCP server
        
        Args:
            num_samples: Number of complex samples to read
            
        Returns:
            Complex numpy array of IQ samples, or None on error
        """
        if not self.connected:
            return None
        
        try:
            bytes_needed = num_samples * 2  # 2 bytes per sample (I and Q)
            data = b''
            
            while len(data) < bytes_needed:
                chunk = self.socket.recv(min(65536, bytes_needed - len(data)))
                if not chunk:
                    return None
                data += chunk
            
            # convert bytes to IQ samples
            raw = np.frombuffer(data[:bytes_needed], dtype=np.uint8)
            i_samples = (raw[0::2] - 127.5) / 127.5
            q_samples = (raw[1::2] - 127.5) / 127.5
            
            return i_samples + 1j * q_samples
            
        except Exception:
            return None
    
    @staticmethod
    def mhz_to_hz(freq_mhz):
        """Convert MHz to Hz"""
        return int(freq_mhz * 1e6)
    
    @staticmethod
    def hz_to_mhz(freq_hz):
        """Convert Hz to MHz"""
        return freq_hz / 1e6
    
    def configure(self, freq_mhz=100.0, sample_rate=1024000, gain_db=30.0, use_agc=False, ppm=0):
        """
        Configuration helper
        
        Args:
            freq_mhz: Frequency in MHz
            sample_rate: Sample rate in Hz (default 1.024 MHz)
            gain_db: Gain in dB (ignored if use_agc=True)
            use_agc: Use automatic gain control
            ppm: Frequency correction in PPM
        """
        if not self.connected:
            return False
        
        success = True
        success &= self.set_sample_rate(sample_rate)
        success &= self.set_freq_correction(ppm)
        success &= self.set_frequency(self.mhz_to_hz(freq_mhz))
        
        if use_agc:
            success &= self.set_gain_mode(manual=False)
        else:
            success &= self.set_gain_mode(manual=True)
            success &= self.set_gain(gain_db)
        
        return success


# Usage example, change to True or remove the if to use it
if False:
    # Create client
    rtl = RTLTCPClient('localhost', 1234)
    
    # Connect
    if rtl.connect():
        # Configure for FM radio at 100 MHz
        rtl.configure(freq_mhz=100.0, sample_rate=1024000, gain_db=30.0)
        
        # Read some samples
        samples = rtl.read_samples(65536)
        if samples is not None:
            print(f"Got {len(samples)} samples")
            print(f"Sample mean: {np.mean(samples)}")
        
        # Clean up
        rtl.disconnect()