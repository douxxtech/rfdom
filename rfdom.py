from typing import List, Optional
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
    
    
    def __reseed(self) -> None:
        seeder_seed: int = self.__seeder.seed.int

        if self.__last_seed != seeder_seed:
            self.__last_seed = seeder_seed
            self.__lcg.reseed(seeder_seed)