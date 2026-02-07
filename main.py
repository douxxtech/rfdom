from rfdom import RFDom

random = RFDom(host="192.168.1.185")

dotrandom = random.random()
dotuniform = random.uniform(0, 19.69)
dotrandint = random.randint(0, 20)
dotrandrange = random.randrange(20)
dotchoice = random.choice([1, 2, 3, 4, 5, ":3", 69])
dotchoices = random.choices([1, 2, 3, 4, 5], k=2)
dotsample = random.sample([1, 2, 3, 4, 5], k=2)
dotshuffle = [1, 2, 3, 4, 5]
random.shuffle(dotshuffle)
dotgauss = random.gauss(5, 3)
dotexpovariate = random.expovariate(5)

print(f".random() -> {dotrandom}")
print(f".uniform(0, 19.69) -> {dotuniform}")
print(f".randint(0, 20) -> {dotrandint}")
print(f".randrange(20) -> {dotrandrange}")
print(f".choice([1, 2, 3, 4, 5, ':3', 69]) -> {dotchoice}")
print(f".choices([1, 2, 3, 4, 5], k=2) -> {dotchoices}")
print(f".sample([1, 2, 3, 4, 5], k=2) -> {dotsample}")
print(f".shuffle([1, 2, 3, 4, 5]) -> {dotshuffle}")
print(f".gauss(5, 3) -> {dotgauss}")
print(f".expovariate(5) -> {dotexpovariate}")