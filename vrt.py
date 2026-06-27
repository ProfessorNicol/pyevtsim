import random

# vtUnits gives exp where 10^{exp} is the number of seconds to a tick.
# -9 is nanosec, -6 is musec, -3 is msec, 0 is sec
#
vtUnits = -9

# vtToSecs is multiplied times the number of ticks to convert to the number of seconds.
vtToSecs = float(10**vtUnits)

# secsToVt is multiplied times the number of seconds to convert to the number of ticks.
secsToVt = 1.0 / (10**vtUnits)

# When creating instances of virtual time we often start with zero ticks and
# want to be sure that the factory methods recognize it as an integer.
#
IntZero = int(0)

# The VT class represents virtual time as discrete ticks, with a time-breaking
# priority. When two vrtTime representations have the same number of ticks, like time, the one
# with small priority value is selected before the one with larger priority value.
#
# One can create an instance of a vrtTime object passing in a floating point number of 'seconds',
# or an integer number of ticks.   If created with seconds the corresponding number of ticks
# is obtained through method SecsToTicks, which uses a tunable scaling factor of the
# number of ticks per second.  When a priority of 0 is passed in it is replaced with
# a randomized priority which is useful when one does not want deterministic
# tie-breakers of events with the same time


# PriPair is the base class for VT.


class PriPair():
    def __init__(self, primary, secondary):
        self.primary = primary
        self.secondary = secondary

    # The __lt__ function is needed to allow 3rd party packages
    # to compare two PriPair instances a and b, and determine whether
    # a < b.
    #
    def __lt__(self, pp):
        if self.primary < pp.primary:
            return True
        elif self.primary > pp.primary:
            return False

        return self.secondary < pp.secondary


# The VT class is the interface used by other simulation modules.
# Given that it derives from PriPair which handles comparisons of
# virtual times, VT primarily provides an API for various conversions.


class VT(PriPair):
    # the base constructor is given ticks.  If no priority is specified it is assumed to be zero,
    # triggering a randomized assignment
    def __init__(self, ticks: int, pri: int):
        if pri == 0:
            pri = int(random.random() * 100000) + 1

        super().__init__(ticks, pri)

    # getTicks returns the ticks component of a VT
    def getTicks(self):
        return self.primary

    # getPri returns the priority tie-breaking component of a VT
    def getPri(self):
        return self.secondary

    # setTicks allows a user to specify the ticks component of a VT
    def setTicks(self, ticks):
        self.primary = ticks

    # setPri allows a user to specify the priority tie-breaking component of a VT
    def setPri(self, pri):
        self.secondary = pri

    # from_ticks is the constructor when the VT is
    # created using integer ticks.  No specification of priority
    # triggers randomized priority.  Priority of -1 means
    # priority to be over-ridden when event time is combined with another,
    # e.g., when adding them
    @classmethod
    def from_ticks(cls, ticks: int, pri=0):
        return cls(ticks, pri)

    # from_secs is the constructor when the vrtTime is
    # created using seconds.  No specification of priority
    # triggers randomized priority
    @classmethod
    def from_secs(cls, secs: float, pri=0):
        ticks = int(round(secs * secsToVt, 1))
        return cls(ticks, pri)

    # TicksToSecs converts a tick representation to seconds, primarily
    # for reporting.

    @staticmethod
    def TicksToSecs(ticks: int) -> float:
        return ticks * vtToSecs

    # TicksToSecs converts a seconds representation to ticks, primarily
    # for storing the time.

    @staticmethod
    def SecsToTicks(sec: float) -> int:
        return int(round(sec * secsToVt, 1))

    # Event scheduling uses a time value into the future, which must be added
    # to the current time to create the event time.   Method Add
    # is used. Of the two, the positive priority that is highest (meaning least value)
    # is saved.

    def Add(self, vt):
        self.setTicks(self.getTicks()+vt.getTicks())
        if vt.getPri() > -1 or self.getPri() > -1:
            self.setPri(max(self.getPri(), vt.getPri()))
        return self

    # Copy returns a replica that uses different memory and so is unaffected
    # by changes to the source object.

    def Copy(self):
        return VT.from_ticks(self.getTicks(), self.getPri())

    # InSeconds returns the floating point equivalent of the number of ticks

    def InSeconds(self):
        return self.TicksToSecs(self.getTicks())


# we sometimes need a zero value for virtual time, can use VTZero

VTZero = VT(0, 1)
