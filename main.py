from rtltcpclient import RTLTCPClient
from seeder import Seeder
import time

client = RTLTCPClient('192.168.1.185')

seeder = Seeder(client)

while True:
    print(seeder.seed)
    time.sleep(5)