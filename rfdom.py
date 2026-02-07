from typing import List, Optional, overload, Sequence, MutableSequence
from utils.rtltcpclient import RTLTCPClient
from utils.seeder import Seeder
from utils.LCG import LCGPseudoRandomGenerator
import math

class RFDom:
    """
    Hardware random number generator using radio frequency noise from RTL-SDR.
    
    RFDom provides a drop-in replacement for Python's random module that generates
    cryptographically strong random numbers from atmospheric radio noise. It uses
    an RTL-SDR device to capture IQ samples across a frequency range, converts them
    to seeds via phase angle analysis and SHA-256 hashing, and feeds these into an
    LCG for deterministic random number generation.
    
    The seeder continuously refreshes in a background thread, automatically reseeding
    the LCG when new entropy is available from the RF environment.
    
    Args:
        host: RTL-TCP server hostname (default "localhost").
        port: RTL-TCP server port (default 1234).
        gain: RTL-SDR gain in dB (default 49.6).
        freq_range: Frequency range to scan [min_MHz, max_MHz] (default [110, 120]).
        num_samples: Number of IQ samples per seed generation (default 120).
        refresh_rate: Seed refresh interval in milliseconds (default 5000).
    
    Raises:
        Exception: If connection to RTL-TCP server fails or initial seed cannot be generated.
    
    Example:
        >>> rng = RFDom(host="192.168.1.100", gain=40.0)
        >>> rng.randint(1, 100)
        42
        >>> rng.choice(['heads', 'tails'])
        'heads'
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 1234,
        gain: Optional[float] = None,
        freq_range: Optional[list] = None,
        num_samples: Optional[int] = None,
        refresh_rate: Optional[int] = None,
    ) -> None:
        """
        Initialize the RFDom hardware random number generator.
        
        Establishes connection to an RTL-TCP server, configures the RTL-SDR device,
        generates an initial seed from RF noise, and starts the background seeder
        thread for continuous entropy collection.
        
        Args:
            host: RTL-TCP server hostname (default "localhost").
            port: RTL-TCP server port (default 1234).
            gain: RTL-SDR gain in dB (default 49.6).
            freq_range: Frequency range [min_MHz, max_MHz] (default [110, 120]).
            num_samples: IQ samples per seed (default 120).
            refresh_rate: Seed refresh interval in ms (default 5000).
        
        Raises:
            Exception: If RTL-TCP connection fails or initial seeding fails.
        """
        
        try:
            client = RTLTCPClient(host, port)
            self.__seeder: Seeder = Seeder(
                client,
                gain if gain is not None else 49.6,
                freq_range if freq_range is not None else [110, 120],
                num_samples if num_samples is not None else 120,
                refresh_rate if refresh_rate is not None else 5000,
            )

            self.__last_seed = self.__seeder.seed.int

            self.__lcg: LCGPseudoRandomGenerator = LCGPseudoRandomGenerator(
                a=1103515245,
                c=12345,
                m=2**31,
                seed=self.__last_seed
            )

        except:
            raise


    def random(self) -> float:
        """
        Generate a random float in the range [0.0, 1.0).
        
        Returns:
            float: A random floating-point number between 0.0 (inclusive) and 1.0 (exclusive).
        """

        self.__reseed()

        return self.__lcg.get_float()
    
    
    def uniform(self, a: float, b: float) -> float:
        """
        Generate a random float in the range [a, b].
        
        Args:
            a: Lower bound (inclusive).
            b: Upper bound (inclusive).
        
        Returns:
            float: A random floating-point number between a and b (both inclusive).
        """

        self.__reseed()

        val1: float = a
        val2: float = b

        if (val1 > val2): # inversion check
            val2 = a
            val1 = b

        # Get a random float in [0.0, 1.0] and scale it to [val1, val2]
        random = self.__lcg.get_float(inclusive=True)
        return val1 + (val2 - val1) * random
    

    def randint(self, a: int, b: int) -> int:
        """
        Generate a random integer in the range [a, b].
        
        Args:
            a: Lower bound (inclusive).
            b: Upper bound (inclusive).
        
        Returns:
            int: A random integer between a and b (both inclusive).
        """

        self.__reseed()

        val1: float = a
        val2: float = b

        if (val1 > val2): # inversion check
            val2 = a
            val1 = b

        return self.__lcg.get_number([val1, val2], inclusive=True)
    
    def randrange(self, start: int, stop: int = None, step: int = 1):
        """
        Generate a random integer from range(start, stop, step).
        
        Args:
            start: Starting value (or stop if stop is None).
            stop: Stopping value (exclusive). If None, range is [0, start).
            step: Step size (default 1).
        
        Returns:
            int: A random integer from the range.
        
        Raises:
            ValueError: If step is 0 or the range is empty.
        """

        if step == 0:
            raise ValueError("step argument must not be zero")

        if stop is None:
            # randrange(stop) -> randrange(0, stop, 1)
            stop = start
            start = 0

        # Calculate how many valid values exist
        if step > 0:
            # Counting up: start, start+step, start+2*step, ...
            # How many steps until we reach/exceed stop?
            n = (stop - start + step - 1) // step  # ceiling division
        else:
            # Counting down: start, start+step (negative), ...
            # How many steps until we go below stop?
            n = (stop - start + step + 1) // step  # ceiling division (step is negative)

        if n <= 0:
            raise ValueError("empty range for randrange()")
        
        return start + step * self.randint(0, n - 1)
    

    def choice(self, seq: Sequence[type]) -> type:
        """
        Choose a random element from a non-empty sequence.
        
        Args:
            seq: A non-empty sequence.
        
        Returns:
            A random element from the sequence.
        
        Raises:
            ValueError: If the sequence is empty.
        """

        length = len(seq)
        
        if length == 0:
            raise ValueError("cannot choose from an empty sequence")

        return seq[self.randint(0, length - 1)]


    def choices(self, population: Sequence[type], weights: Optional[Sequence[type]] = None, cum_weights: Optional[Sequence[float]] | None = None, k: int = 1) -> List[type]:
        """
        Choose k elements from population with replacement, optionally weighted.
        
        Args:
            population: Sequence to choose from.
            weights: Optional weights for each element.
            cum_weights: Optional cumulative weights (mutually exclusive with weights).
            k: Number of elements to choose (default 1).
        
        Returns:
            List of k chosen elements.
        
        Raises:
            ValueError: If population is empty, k < 1, or weight counts don't match.
        """

        pop_length = len(population)

        if pop_length == 0:
            raise ValueError("cannot choose from an empty sequence")
        
        if k < 1:
            raise ValueError("k must be at least 1")
        
        elements: Sequence[type] = []

        if weights is None and cum_weights is None:
            for _ in range(k):
                elements.append(population[self.randint(0, pop_length - 1)])
            
            return elements

        # process cumulative weights if not already given
        if cum_weights is None:
                    
            if pop_length != len(weights):
                raise ValueError("one weight per population element is required")
            
            cum_weights = []
            total = 0

            for w in weights:
                total += w
                cum_weights.append(total) # If given [1, 3, 2, 4], cum_weights will contain [1, 4, 6, 10]

        else:

            if pop_length != len(cum_weights):
                raise ValueError("one weight per population element is required")
            
        for _ in range(k):
            random = self.uniform(0, cum_weights[-1])
            index = next(i for i, cw in enumerate(cum_weights) if random < cw)
            elements.append(population[index])

        return elements
    

    def sample(self, population: Sequence[type], k: int, counts: Optional[Sequence[int]] = None) -> List[type]:
        """
        Choose k unique elements from population without replacement.
        
        Args:
            population: Sequence to sample from.
            k: Number of elements to choose.
            counts: Optional counts representing how many times each element appears.
        
        Returns:
            List of k unique elements in sorted order by original index.
        
        Raises:
            ValueError: If k > population size, counts are negative, or count mismatch.
        """

        pop_length = len(population)

        if counts is not None:
            if len(counts) != pop_length:
                raise ValueError("one count per population element is required")
            
            if any(count < 0 for count in counts):
                raise ValueError("counts must be non-negative")
            
            weights = list(counts)

        else:
            weights = [1] * pop_length

        if k > pop_length:
            raise ValueError("k cannot be bigger than population")

        chosen_indices = []

        for _ in range(k):
            total_weight = sum(weights)
            random = self.randint(1, total_weight)

            acc = 0
            for i, w in enumerate(weights):
                acc += w
                if acc >= random:
                    chosen_indices.append(i)
                    weights[i] = 0
                    break

        chosen_indices.sort()
        return [population[i] for i in chosen_indices]

    def shuffle(self, x: MutableSequence):
        """
        Shuffle a mutable sequence in-place using Fisher-Yates algorithm.
        
        Args:
            x: A mutable sequence to shuffle.
        """

        n = len(x)
        for i in range(n):
            j = self.randint(i, n - 1)
            x[i], x[j] = x[j], x[i]


    def gauss(self, mu: float, sigma: float) -> float:
        """
        Generate a random number from Gaussian (normal) distribution.
        
        Uses Box-Muller transform to generate normally distributed values.
        
        Args:
            mu: Mean of the distribution.
            sigma: Standard deviation (must be >= 1).
        
        Returns:
            float: A random value from the Gaussian distribution.
        
        Raises:
            ValueError: If sigma < 1.
        """

        if sigma < 1:
            raise ValueError("sigma must be 1 or superior")

        u1 = self.random()
        u2 = self.random()

        z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
        
        return mu + sigma * z
    
    def expovariate(self, lambd: float) -> float:
        """
        Generate a random number from exponential distribution.
        
        Args:
            lambd: Rate parameter (lambda), must be > 0.
        
        Returns:
            float: A random value from the exponential distribution.
        
        Raises:
            ValueError: If lambd <= 0.
        """

        if lambd <= 0:
            raise ValueError("lambda must be > 0")
        
        u = self.random()

        return -math.log(u) / lambd

    def __reseed(self) -> None:
        seeder_seed: int = self.__seeder.seed.int

        if self.__last_seed != seeder_seed:
            self.__last_seed = seeder_seed
            self.__lcg.reseed(seeder_seed)


    @overload
    def randrange(self, stop: int) -> int: ...

    @overload
    def randrange(self, start: int, stop: int) -> int: ...

    @overload
    def randrange(self, start: int, stop: int, step: int) -> int: ...