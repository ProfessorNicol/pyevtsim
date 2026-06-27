"""
.. _statspy:

stats.py
========

Summary
-------

The stats module provides an interface for gathering observations during
the execution of a simulation, and at the end of the simulation
performing simple statistical analysis. Individual objects in a
simulation create instances of the ``Trace`` class through which
observations are reported. Indeed the only significant data structure in
a ``Trace`` instance is a list of ``Observation``'s, added by calls to
the ``Trace`` method ``AddObs(self, action, time, objectID)``

.. code:: 

   class Trace():
       def __init__(self, name: str):
           self.name = name
           self.observations = []

       # AddObs is called to create an observation and append it to the
       # trace's list of observations.

       def AddObs(self, action: str, time: float, objectID: int):
           label = action
           # insure that observation label is one of ('start', 'stop')
           if action in ('start', 'Start', 'begin', 'Begin'):
               label = 'start'
           if action in ('stop', 'Stop', 'end', 'End'):
               label = 'stop'

   				# create and store new observation
           obs = Observation(label, time, objectID)
           self.observations.append(obs)

The ``stats.py`` logic assumes that in any given instance of a
``Trace``, for any given ``objectID`` , there will a ``start``
observation and possibly (but not necessarily) a ``stop`` observation
that occurs with a ``time`` value that is no smaller than the ``time``
value on the corresponding ``start`` observation. When an ``objectID``
has both ``start`` and ``end`` observations, the difference between the
times on the ``stop`` and ``start`` observations is taken as a "sample".
Typically the ``start`` observation is taken when the object enters some
subsystem or service, and the ``stop`` observation when it leaves, so
the sample is measuring how long (in simulation time) is resident
somewhere in the system.

A user calls the ``Trace`` method
``StatSummary(self, skipFrac=0.1)``\ to compute and print the results of
an analysis that computes the mean and standard deviation of all samples
associated with the ``Trace`` . The (optional) parameter ``skipFrac``
tells the method what fraction of samples at the begining of the trace
to skip before doing the analysis of mean and standard deviation. This
is a simple (but incomplete) way to begin to deal with the problem of
initialization bias.
"""


import math

# Every observation gets a unique ID, obtained by calling nxtObsID()

obsID = 0
def nxtObsID():
    global obsID
    obsID += 1
    return obsID


# The Observation class holds an instance where a obs_type
# (from {'start','stop'} is included, a time of the observation is 
# included, and a unique identity code for the observed object is
# included.

class Observation():
    def __init__(self, obs_type, time, objectID):
        self.obsID = nxtObsID()
        self.obs_type = obs_type
        self.objectID = objectID
        self.time = time


# A Trace object holds a sequence of observations, and provides 
# an API for analyzing them.

class Trace():
    def __init__(self, name):
        self.name = name
        self.observations = []

    # AddObs is called to create an observation and append it to the
    # trace's list of observations.

    def AddObs(self, action: str, time: float, objectID: int):
        label = action

        # insure that observation label is one of ('start', 'stop')
        if action in ('start', 'Start', 'begin', 'Begin'):
            label = 'start'
        if action in ('stop', 'Stop', 'end', 'End'):
            label = 'stop'
    
        # create and store new observation
        obs = Observation(label, time, objectID)
        self.observations.append(obs)

    # gatherSamples is called after all the observations have been
    # gathered and stored. It matches the 'start' and 'stop' observations
    # for each object (assuming that each object has at most one pair 
    # of associated observations), computes the difference between the stop time
    # and the start time, and returns a list of those differences.  These are the
    # observed lengths of time objects spend in whatever construct is gathering the trace.

    def gatherSamples(self):

        # samples will be the returned list
        samples = []

        # For every objectID we encounter we will create a dictionary
        # entry indexed by that objectID, used to identify a list of observations
        # in self.observations labeled with that objectID.  Nominally there will be
        # two of these, a 'start' and a 'stop'.
        entities = {}

        # create the entities dictionary
        for obs in self.observations:

            # if this is the first encounter with the objectID then
            # create a new dictionary entry
            objID = obs.objectID
            if objID not in entities:
                entities[objID] = []

            # add the observation to the list associated with its objectID
            entities[objID].append(obs)

         
        for eID in entities:
            obsList = entities[eID]

            # some entities will have started but the simulation ends before
            # stop.  Skip those

            if len(obsList) < 2:
                continue

            # The assumption is made that an object always 'stops' before
            # 'starting' again, if even starting again is possible. This
            # means that a 'start' obs_type is followed by a 'stop' 
            #   Step through the obsList by adjacent pairs
            #
            for idx in range(0, len(obsList), 2):
                obs0 = obsList[idx]
                obs1 = obsList[idx+1]
                if obs0.obs_type == 'start' and obs1.obs_type == 'stop':
                    # save the difference as a sample
                    samples.append(obs1.time-obs0.time)
                else:
                    print("observation gathering fault")

        return samples

    # StatSummary computes the mean and standard deviation of the
    # samples, skipping the first skipFrac of entries to account 
    # for initialization bias

    def StatSummary(self, skipFrac=0.1):
        sum = 0.0
        sum2 = 0.0
        samples = self.gatherSamples()

        # Compute the range of samples over which we take statistics.
        start = int(len(samples)*skipFrac)
        n = len(samples)-start

        # Sum the samples and the squared samples in prep for
        # taking the mean and standard deviation
        # 
        for idx in range(start, len(samples)):
            sum += samples[idx]

        if n > 1:
            # compute the average of the samples and average of the samples squared
            mean = sum / n

            sum = 0.0
            for idx in range(start, len(samples)):
                s = samples[idx]
                sum += (s-mean)*(s-mean)
       
            var = sum/(n-1) 
            std = math.sqrt(var)

            print(
                f"{self.name} trace with {n} samples, mean {mean} with standard deviation {std}")

        else:
            print(f"{self.name} trace has insufficient samples")
