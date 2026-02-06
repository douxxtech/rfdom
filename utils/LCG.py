class LCGPseudoRandomGenerator:
    """
    Linear Congruential Generator (LCG) for pseudo-random number generation.
    
    Implements the LCG algorithm using the recurrence relation:
        X(n+1) = (a * X(n) + c) mod m
    
    This generator produces a deterministic sequence of pseudo-random numbers
    based on an initial seed. The quality of randomness depends on the choice
    of parameters a, c, and m.
    
    Attributes:
        a (int): Multiplier coefficient.
        c (int): Increment coefficient.
        m (int): Modulus (defines the period of the generator).
        x0 (int): Initial seed value.
        x_prev (int): Previous state value used for generation.
    """
    
    def __init__(self, a: int, c: int, m: int, seed: int):
        """
        Initialize the Linear Congruential Generator.
        
        Args:
            a (int): Multiplier coefficient (should be positive).
            c (int): Increment coefficient (should be non-negative).
            m (int): Modulus (should be positive, typically a power of 2).
            seed (int): Initial seed value for the generator.
        
        Note:
            Common parameter sets include:
            - glibc: a=1103515245, c=12345, m=2^31
            - Numerical Recipes: a=1664525, c=1013904223, m=2^32
        """
        
        self.a: int = a
        self.c: int = c
        self.m: int = m
        self.x0: int = seed
        self.x_prev: int = (self.a * self.x0 + self.c) % self.m
    
    def get_number(self, num_range=None, inclusive: bool = False) -> int:
        """
        Generate the next pseudo-random number in the sequence.
        
        Advances the internal state and returns either the raw value or
        a value scaled to fit within a specified range.
        
        Args:
            num_range (tuple[int, int], optional): A tuple (min, max) defining
                the output range. If None, returns the raw generated value.
            inclusive (bool): If True, the upper bound is inclusive [min, max].
                            If False (default), upper bound is exclusive [min, max).
        
        Returns:
            int: The next pseudo-random number. If num_range is provided,
                returns a value in the specified range. If None, returns a value
                in [0, m).
        """

        self.x_prev: int = (self.a * self.x_prev + self.c) % self.m
        
        if num_range is None:
            return self.x_prev
        else:
            if inclusive:
                # [min, max] = (max - min + 1) possible values
                return num_range[0] + int((self.x_prev / self.m) * (num_range[1] - num_range[0] + 1))
            else:
                # [min, max) = (max - min) possible values
                return num_range[0] + int((self.x_prev / self.m) * (num_range[1] - num_range[0]))
        

    def get_float(self, inclusive: bool = False) -> float:
        """
        Generate the next pseudo-random float.
        
        Advances the internal state and returns a normalized floating-point
        value.
        
        Args:
            inclusive (bool): If True, returns range [0.0, 1.0] (both bounds inclusive).
                            If False (default), returns range [0.0, 1.0) (upper bound exclusive).
        
        Returns:
            float: A pseudo-random float in the specified range.
        """

        self.x_prev: int = (self.a * self.x_prev + self.c) % self.m
        
        if inclusive:
            return self.x_prev / (self.m - 1)
        else:
            return self.x_prev / self.m
        
    def reseed(self, new_seed: int) -> None:
        """
        Re-initialize the generator with a new seed value.
        
        Resets the generator's internal state using a new seed. This is useful
        for periodically injecting fresh entropy from external sources while
        maintaining continuous operation.
        
        Args:
            new_seed (int): The new seed value to initialize the generator with.
        
        Note:
            After reseeding, the sequence will be deterministic based on the
            new seed until the next reseed operation.
        """

        self.x0 = new_seed
        self.x_prev = (self.a * self.x0 + self.c) % self.m