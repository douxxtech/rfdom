from rfdom import RFDom

random = RFDom(host="192.168.1.185")

dotrandom = random.random()
dotuniform = random.uniform(0, 19.69)

print(f".random() -> {dotrandom}")
print(f".uniform(0, 19.69) -> {dotuniform}")