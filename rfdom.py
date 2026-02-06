from typing import List, Optional, overload, Sequence
from utils.rtltcpclient import RTLTCPClient
from utils.seeder import Seeder
from utils.LCG import LCGPseudoRandomGenerator

class RFDom:
    """
    Docstring for RFDom
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
        self.__reseed()

        return self.__lcg.get_float()
    
    
    def uniform(self, a: float, b: float) -> float:
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
        self.__reseed()

        val1: float = a
        val2: float = b

        if (val1 > val2): # inversion check
            val2 = a
            val1 = b

        return self.__lcg.get_number([val1, val2], inclusive=True)
    
    def randrange(self, start: int, stop: int = None, step: int = 1):
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
        length = len(seq)
        
        if length == 0:
            raise ValueError("cannot choose from an empty sequence")

        return seq[self.randint(0, length - 1)]


    def choices(self, population: Sequence[type], weights: Optional[Sequence[type]] = None, cum_weights: Optional[Sequence[float]] | None = None, k: int = 1):
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

    def __reseed(self) -> None:
        seeder_seed: int = self.__seeder.seed.int

        if self.__last_seed != seeder_seed:
            self.__last_seed = seeder_seed
            self.__lcg.reseed(seeder_seed)