# RFDom

Hardware random number generator using radio frequency noise from RTL-SDR devices.

[Blog article here](https://douxx.blog/how-i-built-a-random-number-generator-sort-of)

## Overview

RFDom provides a drop-in replacement for Python's `random` module that generates cryptographically strong random numbers from atmospheric radio noise. It uses an RTL-SDR device to capture IQ samples, converts them to seeds via phase angle analysis and SHA-256 hashing, and feeds these into an LCG for deterministic random number generation.

## Requirements

- RTL-SDR device
- RTL-TCP server running (e.g., `rtl_tcp -a 0.0.0.0`)
- Python 3.x

## Installation

```bash
pip install rfdom
```

Or from source:

```bash
git clone https://github.com/douxxtech/rfdom.git
cd rfdom
pip install -e .
```

## Usage

```python
from rfdom import RFDom

# Connect to RTL-TCP server
rng = RFDom(host="192.168.1.185", gain=49.6)

# Use like Python's random module
print(rng.random())                 # 0.0 to 1.0 [0.0, 1.0)
print(rng.randint(1, 100))          # Random integer [1, 100]
print(rng.choice(['a', 'b', 'c']))  # Random choice
print(rng.gauss(0, 1))              # Gaussian distribution
```

## Supported Methods

- `random()`, `uniform()`, `randint()`, `randrange()`
- `choice()`, `choices()`, `sample()`, `shuffle()`
- `gauss()`, `expovariate()`

## License

This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details.
