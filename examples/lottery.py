from rfdom import RFDom

rng = RFDom(host="192.168.1.185")

# Generate 6 unique lottery numbers from 1-49
numbers = rng.sample(range(1, 50), k=6)
print(f"Your lottery numbers are: {', '.join(str(n) for n in sorted(numbers))}")