# Module evt holds classes and global variables for
# events and event lists for discrete event simulation.
#
from rng import sampleU01
from queue import PriorityQueue
from vrt import VT

# The Event class stores information about a future event to execute.
# Its attributes include
#   - a positive identity, evt_ID, that is used to refer to the event, e.g., to cancel it
#   - context, some object, typically a pointer to a class object refering to
#     something in the simulation model (like a server)
#   - data, some object, typically a pointer to something specific to be used in executing the event
#   - hndlr, a pointer to a function that is called to execute the event,
#   - desc, a string included to describe the function.  Used only for debugging,
#     handy when trying to see what's coming up on the event list when stepping
#     through execution.


class Event():

    # The EvtFunc structure encapsulates the context, object, and handler
    # associated with the event, argument evt_func is an instance

    def __init__(self, evt_func, vt, desc=""):
        self.evt_ID = nxtEvt_ID()
        self.context = evt_func.context
        self.data = evt_func.data
        self.desc = desc
        self.hndlr = evt_func.hndlr

        # vrtime is an instance of a class, and what is passed is a pointer to
        # the memory where the instance of that class is stored.
        # Make an explicit copy to avoid having other references to that memory
        # object affect this one
        #
        self.vrtime = vt.Copy()

    # use the vrtTime '<' operator to determine the ordering of two events
    # Definition of __lt__ is needed to support instances of the Event class
    # being managed by the python PriorityQueue framework

    def __lt__(self, evt) -> bool:
        return self.vrtime < evt.vrtime


# An EvtList manages an event list that is organized using a python PriorityQueue.
# Its attributes are
#   - the event list priority queue, pq
#   - a dictionary 'pending' recording pending events, indexed by event id,
#     with boolean values which are ignored,
#     presence in the dictionary is the sought for information
#   - a dictionary 'cancel' recording the identities of events that have been tagged to be removed
#   - the vrtTime of the last event executed


class EvtList():
    def __init__(self):

        # Built-in python module PriorityQueue will efficiently organize
        # events to make the cost of getting the one with least next simulation time
        # a constant, and the cost of adding a new event be logarithmic in the number
        # of items in the queue
        #
        self.pq = PriorityQueue()

        # Be able to access events that have been scheduled but not yet executed.
        self.pending = {}

        # Remember the event ID of events that have been cancelled in a dictionary
        # indexed by event ID, looking for residency in that dictionary when an event
        # is selected for execution.
        #
        self.cancel = {}

        # vrtime will hold the virtual time of the last event pulled from the event list.
        # Here initialized to 0
        self.vrtime = VT.from_ticks(0, -1)

        # trace is a flag that when set has the description of each event printed when
        # it is scheduled, and when it is executed.
        #
        self.trace = False

    # Len gives the number of uncancelled events in the queue. The calculation
    # accounts for the method that an event isn't pulled from the priority queue
    # when canceled, but rather, is ignored when it turns up to be the next event
    # to execute.

    def Len(self) -> int:
        return (self.pq.qsize()-len(self.cancel))

    # Empty indicates whether the event list has no uncancelled events in queue

    def Empty(self) -> bool:
        return self.Len() == 0

    # AddEvt is called to schedule an event.  Its calling arguments are
    #  - an instance evt_func of an EvtFunc structure.  That structure holds
    #       * context, a python object typically used to point to some portition of a model
    #         that is being affected by the event.
    #       * data, a python object typically used to provide some specific piece of data, like
    #         a message, to be available to the event handler.
    #       *  hndlr, identity of the function to be called to execute the event.
    #
    #  - offset, the amount of virtual time in the future when the event will be executed.
    #  - desc (optional), which may be included to label an event with a text string
    #    describing what it does and where it does it.

    def AddEvt(self, evt_func, offset: VT, desc=""):

        # Create a version of the event time that will be modified to create
        # the time at which the event execution occurs.
        now = self.vrtime.Copy()

        # Create an event, noting that the offset is added to the current
        # function time to create a vrtTime object with the time of execution,
        # which is what will be used by the event list's priority queue for ordering.
        #
        evtTime = now.Add(offset)
        evt = Event(evt_func, evtTime, desc=desc)

        # Recover the event ID to be returned.
        evtID = evt.evt_ID

        # Put the event in the priority queue
        self.pq.put((evtTime, evt))

        # remember the event ID as pending for execution
        self.pending[evtID] = True

        # If we are tracing, print the description of the event being scheduled.
        if self.trace:
            print(f"> time {self.vrtime.InSeconds()} schedules {evt.desc} \
                for time {evtTime.InSeconds()}")

        # return the ID and the time at which the event will be executed
        return evtID, evtTime

    # For some models an event needs to be cancelled sometime after it has
    # scheduled. What is done is to remember the identity of the event being canceled,
    # and when these bubble up to the top as if to be executed, are removed without
    # being executed.  Indicate with the return whether the event was found to be canceled.

    def CancelEvt(self, evtID: int) -> bool:
        try:
            # it should be the case that the event id is for an event
            # that is pending, if not just ignore the ask
            del self.pending[evtID]

            # note the canceling request in the cancel dictionary
            self.cancel[evtID] = True
            return True
        except:
            # evidently not pending or not pending any longer
            return False

    # rmCancelled removes the canceled events that are highest priority,
    # it always called as part of finding the next event to execute.

    def rmCancelled(self):

        # Loop until we find an event not to cancel or we have exhausted the list.
        # When an event is found that we don't cancel, we just return from within the loop.
        #
        while not self.Empty():

            # get the identity of the event with highest priority to execute
            evtID, _ = self.MinEvt_ID()

            # Receiving None back means the queue is empty, so there is nothing to do.
            if evtID is None:
                return

            # If the event whose ID was returned was canceled,
            # remove the ID from the cancel dictionary and pull the
            # minimum time event from the PriorityQueue
            #
            if evtID in self.cancel:

                # Remove the identity of the canceled event from the cancel dictionary.
                del self.cancel[evtID]

                # Pull that event off the priority queue.
                self.pq.get()

                # Keep going, there may still be more canceled events
                # to remove.
                #
                continue

            else:
                # The next event to execute wasn't canceled, so just return.
                return

    # Minevt_ID returns the event id and time of execution of the
    # highest priority event in the priority queue.  Note that this
    # may include canceled events, because Minevt_ID is called from the
    # routine that cleans the canceled events out

    def MinEvt_ID(self):

        # There is a particularly easy case to deal with...
        if self.Len() == 0:
            return None, None

        # Get a pointer to the highest priorty event struct. Remember
        # that the PriorityQueue manages tuples whose first element
        # is the value used to order, and the second element is the
        # structure being ordered.
        #
        (firstPri, firstEvt) = self.pq.queue[0]

        # return its event ID and time
        return firstEvt.evt_ID, firstEvt.vrtime

    # nxtEvt finds the next uncanceled event to execute,
    # removes it from the priority queue, and returns it

    def nxtEvt(self):

        # First get rid of canceled events at the front of the priority queue.
        self.rmCancelled()

        # If now the priority queue is empty we have nothing to return, nothing to do.
        if self.Empty():
            return None

        # We have something to do! The highest priority element is uncanceled and the next to
        # be executed.  Get it off the priority queue.
        #
        (evt_time, evt) = self.pq.get()

        # The event list remembers the virtual time of the last uncanceled event pulled off
        # the list.
        self.vrtime = evt_time

        # this event is no longer pending so remove it from the pending dictionary
        del self.pending[evt.evt_ID]

        # return the event (remember that the Event structure holds the event time)
        return evt

    # Now returns the time of the last event pulled from the event list

    def Now(self) -> VT:
        return self.vrtime

    # Often we don't want the tie-breaking priority value from vrtime,
    # and want the time as a floating point number with units of seconds
    # rather than 'ticks'.   VT has a ticks to seconds conversion function we call.

    def NowInSecs(self) -> float:
        return VT.TicksToSecs(self.vrtime.getTicks())

    # Run is called to start the simulation run, passing in the simulation time
    # beyond which we will not proceed, and optionally an indicator that we want
    # a printed trace of event descriptions when scheduled and when executed.

    def Run(self, termination, trace=False):

        # Remember the decision to trace or not
        self.trace = trace

        # transform the termination time (in seconds) to VT virtual time,
        # including the highest priority tie-breaker fields which means
        # that an event with the same number of ticks as termination has
        # will be executed.
        #
        VT_termination = VT.from_secs(termination, pri=1)

        # Now keep executing events so long as there are events to execute
        # that have simuation times no greater than VT_termination
        #
        while self.Len() > 0:

            # Pull the next uncancelled event from the event list.
            nxtEvt = self.nxtEvt()

            # Test whether its time dominates VT_termination, and exit if it does.
            if VT_termination < nxtEvt.vrtime:
                return

            # Get the pointer to a method to execute associated with this event.
            hndlr = nxtEvt.hndlr

            # Print a trace if so configured.
            if self.trace:
                print(f"> time {self.vrtime.InSeconds()} runs {nxtEvt.desc}")

            # Call the event handling function, passing the context and data fields
            # from the event struct.
            hndlr(nxtEvt.context, nxtEvt.data)


# EventFunc holds the non-temporal attributes of an Event class
# Code that is scheduling an event creates an instance of this and populates
# it with those attributes.

class EvtFunc():
    def __init__(self, context, data, hndlr):
        self.context = context
        self.data = data
        self.hndlr = hndlr


# Each event gets a unique non-negative integer identifier.
# We can isolate the implementation by providing a method nxtEvt_ID
# to call which provides a unique ID to associate with an event.

evt_ID = 0


def nxtEvt_ID() -> int:
    global evt_ID

    # every call adds one to the running count, to ensure that event IDs are unique
    evt_ID += 1
    return evt_ID

# EvtMgr is a global variable, accessed by all the code that schedules events.


EvtMgr = EvtList()
