import math
import random

# sampleU01 is as basic as it comes, a uniform (0,1] generator
# Uses python's own random module

def sampleU01() -> float:
    return random.random()

# sampleExponon returns a sample from the exponential distribution,
# with rate that is given by the calling argument

def sampleExpon(rate: float) -> float:
    return random.expovariate(rate)

# sampleInt(a,b) returns a sample with integer values drawn uniformly
# among all values from a to b, inclusive.

def sampleInt(a, b : int) -> int:
    return random.randint(a, b)

# sampleRV can return random samples from a number of distributions,
# the particular one selected by the string in argument 'distrb'.
# The mean and standard deviation are provided to shape the selected
# distribution to have those attributes.
#  Possible selections are
#   - expon, which isn't rigorously needed because we have sampleExpon,
#     and indeed call it.
#   - uniform, which draws a continuous uniform from the range [a,b], where
#     a and b are chosen to yield mean mu and standard deviations rho.
#   - gaussian, which draws either from a pristine Gaussian distribution
#     with specified mean and standard deviation, or when the optional parameter
#     'positive' is true, returns a sample from a Gaussian with those parameters
#     but with negative values rejected
#
def sampleRV(mu, rho :float, distrb: str, positive=False) -> float:
    match distrb:
        case "expon":
            return sampleExpon(1.0/mu)
        case "uniform":
            (a, b) = uniform_range(mu, rho)
            return a + sampleU01()*(b-a)
        case "gaussian":
            rv = random.gauss(mu, rho)
            if not positive:
                return rv
            while rv < 0.0:
                rv = random.gauss(mu, rho)

            return rv

# uniform_range computes and returns the values a and b that define
# the limits of a continuous uniform [a,b] random variable with
# specified mean mu and standard deviation rho.

def uniform_range(mu: float, rho: float) -> float:
    """Return [a, b] for a uniform distribution with mean mu and std dev rho."""
    if rho < 0:
        raise ValueError("Standard deviation rho must be non-negative.")

    half_width = math.sqrt(3) * rho
    return mu - half_width, mu + half_width
