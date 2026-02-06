from utils.rtltcpclient import RTLTCPClient
from utils.seeder import Seeder
from utils.LCG import LCGPseudoRandomGenerator
import time

client = RTLTCPClient('192.168.1.185')
seeder = Seeder(client)

last_seed = seeder.seed.int
lcg = LCGPseudoRandomGenerator(a=1103515245, c=12345, m=2**31, seed=last_seed) # using glibc values

try:
    while True:
        print(lcg.get_float())
        
        current_seed = seeder.seed.int
        if current_seed != last_seed:
            lcg.reseed(current_seed)
            last_seed = current_seed
            print("Fresh entropy injected")
        
        time.sleep(1)
        
except KeyboardInterrupt:
    seeder.stop()