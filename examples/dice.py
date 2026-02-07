from rfdom import RFDom

rng = RFDom(host="localhost")

# Roll a six-sided dice
roll = rng.randint(1, 6)
print(f"You rolled: {roll}")