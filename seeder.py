from rtltcpclient import RTLTCPClient
from typing import Optional, List
import time
import hashlib
import math
import threading

class Seeder:
    """
    Generate cryptographic seeds from radio frequency noise using an RTL-SDR device.
    
    The Seeder class captures IQ samples from atmospheric radio noise across a frequency
    range and converts them into cryptographic-quality random seeds using phase angle
    analysis and SHA-256 hashing. Seeds are continuously refreshed in a background thread.
    
    Attributes:
        running: Whether the seeder is currently active.
        seed: The current SHA-256 seed derived from RF samples (read-only property).
    """

    def __init__(self, rtl_tcp_client: RTLTCPClient):
        """
        Initialize the Seeder with an RTL-TCP client connection.
        
        Sets up the seeder to generate cryptographic seeds from radio frequency samples.
        Configures the RTL-SDR device, retrieves initial samples, and starts a background
        thread for continuous seed refreshing.
        
        Args:
            rtl_tcp_client: An RTLTCPClient instance for communicating with the RTL-TCP server.
        
        Raises:
            ValueError: If connection to the RTL-TCP server fails or initial samples cannot be retrieved.
        """
        
        self.running: bool = False
        self.__seed: Optional[str] = None
        self.__client: RTLTCPClient = rtl_tcp_client
        self.__gain: float = 49.6 # max rtlsdr value
        self.__freq_range: List[int] = [110, 120] # [min_freq, max_freq]
        self.__current_freq: int = self.__freq_range[0]
        self.__samples_count: int = 1024 # we're reading 1024000 samples / s, so this will take ~1ms to retrieve them
        self.__refresh_rate: int = 5000
        self.__thread = threading.Thread(target=self.__runner, daemon=True)
        
        if not self.__client.connect():
            raise ValueError("Could not connect to the RTL-TCP server.")
        
        self.running = True
        
        self.__client.configure(freq_mhz=self.__current_freq, gain_db=self.__gain)
        
        self.__seed = self.__samples_to_seed(self.__client.read_samples(self.__samples_count))

        if self.__seed is None:
            raise ValueError("Could not retrieve samples from the RTL-TCP server.")
        
        self.__thread.start()


    @property
    def seed(self):
        """
        Get the current cryptographic seed.
        
        Returns:
            str: A SHA-256 hash hexdigest representing the current seed derived from RF samples.
        """

        return self.__seed
    

    def stop(self):
        """
        Stop the seeder and disconnect from the RTL-TCP server.
        
        Halts the background thread and closes the connection to the RTL-TCP server.
        """

        self.running = False
        self.__client.disconnect()


    def __get_next_freq(self) -> int:
        """
        Calculate the next frequency in the scanning range.
        
        Increments the current frequency by 1 MHz and wraps back to the minimum
        frequency when the maximum is exceeded.
        
        Returns:
            int: The next frequency in MHz to scan.
        """

        self.__current_freq += 1
        
        # If it exceeds max, wrap back to min
        if self.__current_freq > self.__freq_range[1]:
            self.__current_freq = self.__freq_range[0]
        return self.__current_freq


    def __samples_to_seed(self, samples: Optional[List[complex]]):
        """
        Convert IQ samples to a cryptographic seed using phase angle analysis.
        
        Processes complex IQ samples by:
        1. Computing phase angle deltas between consecutive samples
        2. Converting deltas to bits (1 if positive, 0 if negative)
        3. Applying XOR whitening to balance bit distribution
        4. Packing bits into bytes and hashing with SHA-256
        
        Args:
            samples: A list of complex IQ samples from the RTL-SDR, or None.
        
        Returns:
            str or None: A SHA-256 hash hexdigest if successful, the previous seed if samples
                        are None, or None if the seeder is not running.
        """

        if not self.running: 
            return None
        
        if samples is None:
            return self.__seed
        
        try:
            samples_count: int = self.__samples_count

            bits: List[int] = []
            x = samples # just for better maths readablity, same for n

            for n in range(samples_count):
                current: complex = x[n]
                previous: complex = x[samples_count - 1] if n == 0 else x[n-1]
                
                current_angle: float = math.atan2(current.imag, current.real)
                previous_angle: float = math.atan2(previous.imag, previous.real)

                delta: float = (current_angle - previous_angle + math.pi) % 2 * math.pi - math.pi

                bits.append(1 if delta > 0 else 0)

            # end of the first step. However, during tests, ive witnessed more 1s than 0s (about 200 more). 
            # So we'll then uniformize all this

            # we're going to use XOR:
            # 0 0 -> 0
            # 0 1 -> 1
            # 1 0 -> 1
            # 1 1 -> 0

            for n in range(samples_count):
                current: int = bits[n]
                previous: int = bits[samples_count - 1] if n == 0 else bits[n-1]

                bits[n] = current ^ previous

            # OK, now we're in a more even count of 1 and 0s

            # let's do an integer seed, to then do whatever we want with it.
            # We could just do bits[n] + bits[n+1] + bits[n+...] but we're going
            # to hash it, for our seed to always be the same size
            
            byte_array = []
            for n in range(0, len(bits), 8):
                byte = (
                    bits[n] << 7 |   # << shifts the bit left by 7 positions
                    bits[n+1] << 6 | # << shifts the bit left by 6 positions
                    bits[n+2] << 5 | # << shifts the bit left by 5 positions
                    bits[n+3] << 4 | # << shifts the bit left by 4 positions
                    bits[n+4] << 3 | # << shifts the bit left by 3 positions
                    bits[n+5] << 2 | # << shifts the bit left by 2 positions
                    bits[n+6] << 1 | # << shifts the bit left by 1 position
                    bits[n+7] << 0 | # << shifts the bit left by 0 positions (keeps it)
                    0                # | combines all bits (bitwise OR)
                )

                byte_array.append(byte)

            byte_array = bytes(byte_array)

            return hashlib.sha256(byte_array).hexdigest()
        
        except:
            return self.__seed


    def __runner(self):
        """
        Background thread worker for continuous seed generation.
        
        Continuously cycles through the frequency range, collecting samples and
        updating the seed at the configured refresh rate. Runs until stopped.
        """

        while self.running:
            
            self.__client.configure(freq_mhz=self.__get_next_freq(), gain_db=self.__gain) # configure with the shift

            samples: Optional[List[int]] = self.__client.read_samples(self.__samples_count) # read samples

            if samples is None:
                time.sleep(self.__refresh_rate / 1000)
                continue

            self.__seed = self.__samples_to_seed(samples)
            time.sleep(self.__refresh_rate / 1000)