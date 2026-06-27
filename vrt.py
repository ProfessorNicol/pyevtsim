"""
.. _vrtpy:

vrt.py
======

Summary
-------

The vrt module provides data structures and methods that are used to
represent virtual time in a discrete-event simulation. The basic data
structure is a pair of integers, the first being the primary key in a
comparison between two virtual times, the second being involved only
when the primary keys in a comparison of virtual times are equal.
Virtual time (a,b) is determined to be earlier than virtual time (c,d)
if either a<c, or a==c and b<d . The temporal units for the primary key
are nanoseconds by default. Simulations may use floating numbers to
represent time; there are conversion methods to flip between
representations.

The fundamental reasons for basing virtual time on a pair of integers
are to make it possible to carefully order events that are scheduled to
happen at exactly the same time. The assuredness of "exactly the same
time" is given by making the primary key an integer where exact equality
between primary keys can be tested, and by using the secondary key as a
tie-breaker when the primary keys are identical.

Data Structure
--------------

The base class for a virtual time is a ``PriPair``

.. code:: 

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

As shown, the ``__lt__`` operator implements the two-key comparison. The
double underscore naming convention is needed to make this operator
available to system code that does not know of the ``PriPair`` class but
is used to compare two instances of it.

The ``VT`` class derives from ``PriPair`` and adds a constructor
interface that interprets a secondary key of 0 as meaning that the
secondary key should be randomly sampled. This interface allows us to
choose at random which of two events scheduled to execute at exactly the
same time (i.e. the primary keys of their time-stamps are identical)
will be executed first.

.. code:: 

   class VT(PriPair):
       # the base constructor is given ticks.  If no priority is specified 
       # it is assumed to be zero, triggering a randomized assignment
       def __init__(self, ticks: int, pri: int):
           if pri == 0:
               pri = int(random.random() * 100000) + 1

           super().__init__(ticks, pri)

The keys of a VT instance are thought of as being ``ticks`` (the primary
key) and ``pri`` (the tie-breaker). By default the units associated with
ticks are nano-seconds, but a user can change this by changing the
global variable ``vtUnits``, which is the exponent to which 10 is raised
to give the quantitative value of ticks in seconds. In the base file
``vt.py`` ``vtUnits= -9``, which makes the value of a tick in seconds to
be :math:`10^{-9}`, meaning nano-seconds. Setting ``vtUnits= -3`` would
make the value of a tick a millisecond, and so on.

Class VT offers an API with several methods. One avoids direct access to
a VT instance's keys using methods ``getTicks(self)``, ``getPri(self)``,
``setTicks(self, ticks)``, and ``setPri(self,pri)``. VT also defines
class methods that support conversion.

-  ``from_ticks(cls, ticks: int, pri=0)``. Constructor used when a VT is
   created specifying ticks, but without specifying the priority.

-  ``from_secs(cls, secs: float, pri=0)``. Constructor used when a VT is
   created specifying a floating point. The constructor transforms the
   value of ``secs`` into ticks using the conversion implied by
   ``vtUnits``.

VT provides static methods ``SecsToTicks`` and ``TicksToSecs`` for user
called conversions.

When an event is scheduled, a VT instance describing the amount of time
after the present is given to describe when the event is to be executed.
This means the offset needs to be added to the present time. The VT
method ``Add(self, vt)`` is used to add the instance of a VT included as
argument ``vt`` to the instance of VT that is the base for the method.

VT offers method ``Copy(self)`` to make a memory distinct copy of the
base instance, and method ``InSeconds(self)`` to return the number of
seconds implied by the ``ticks`` component of the base instance.
"""

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
