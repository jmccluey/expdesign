# expdesign, a module with utilities for designing experiments

"""
Use this module to balance experimental conditions.

Conditions are represented by arbitrary codes of any type, which can be
chosen by the user.

A trial is one measurement of the experimental variable(s). A trial
corresponds to one condition. Trials may be broken up into sessions; as
sessions are used here, they are just arbitrary groups of trials. Taking
sessions into account allows you to balance conditions within sessions,
as well as within experiment. If the difference between sessions is
meaningful, and not just a matter of breaking up trials so that
participants don't become fatigued, that should be expressed by using
different condition codes.
"""

import random
import numpy

def balanceTrials(conds, nTrials, shuffleType='all', startPos=None):
    """
    Balance conditions across trials.

    Inputs
    ------
    conds : tuple
        Tuple containing arbitrary labels for trial conditions.
    nTrials : int
        Number of trials.
    shuffleType : {'set'|'all'|'none'}
        Type of randomization of order to use.
    startPos : int
        Indicates the position to start cycling conditions.  If None,
        the position will be chosen randomly.  A random starting
        position will prevent biasing when the number of conditions
        does not divide evenly into the number of trials.

    Outputs
    -------
    trialConds : list
        List of condition labels corresponding to each trial.

    Examples
    --------
    >>> conds = ('A', 'B', 'C')
    >>> balanceConditions(conds, 7, shuffleType='none', startPos=0)
    ['A', 'B', 'C', 'A', 'B', 'C', 'A']
    >>> balanceConditions(conds, 7, shuffleType='all')
    ['C', 'A', 'C', 'C', 'B', 'A', 'B']
    >>> balanceConditions(conds, 6, shuffleType='set')
    ['C', 'B', 'A', 'C', 'A', 'B']
    """

    # get the starting place in the conditions list
    nConds = len(conds)
    if startPos:
        if not startPos in range(nConds):
            raise ValueError("startPos must be a valid index for conds.")
        condInd = startPos
    else:
        condInd = random.choice(range(nConds))
    trialConds = []

    # randomize order within each set of conditions
    if shuffleType=='set':
        if (nTrials % nConds) != 0:
            raise ValueError("For set shuffling, nTrials must be a multiple "
                             "of the number of conditions.")
        
        for i in range(nTrials / nConds):
            # create a set with all conditions
            setConds = []
            for j in range(nConds):
                n = condInd % nConds
                setConds.append(conds[n])
                condInd += 1

            # add this set to the trial list
            random.shuffle(setConds)
            trialConds.extend(setConds)

    else:
        for i in range(nTrials):
            n = condInd % nConds
            trialConds.append(conds[n])
            condInd += 1
        if shuffleType=='all':
            random.shuffle(trialConds)
    return trialConds

def balanceSessions(conds, nTrials, nSessions, shuffleType):
    """
    Balance conditions across sessions.

    Inputs
    ------
    conds : tuple
        Tuple containing arbitrary labels for trial conditions.
    nTrials : int
        Number of trials.
    shuffleType : {'set'|'all'|'none'}
        Type of randomization of order to use within each session.
    startPos : int
        Indicates the position to start cycling conditions.  If None,
        the position will be chosen randomly.  A random starting
        position will prevent biasing when the number of conditions
        does not divide evenly into the number of trials.

    Outputs
    -------
    expConds : tuple : [session][trial]
        Gives the condition codes for each trial.
    """

    # make all trials
    if shuffleType=='set':
        allConds = balanceTrials(conds, nTrials * nSessions, shuffleType='set')
    else:
        allConds = balanceTrials(conds, nTrials * nSessions,
                                 shuffleType='none')

    # use a random starting position for the first session
    expConds = []
    for i in range(nSessions):
        # get the next session's worth of trials
        sessConds = allConds[0:nTrials]
        del allConds[0:nTrials]

        if shuffleType=='all':
            random.shuffle(sessConds)
        expConds.append(sessConds)
    return expConds

def balanceNestedConditions(conds, nTrials, nSessions, shuffleType='all'):
    """
    Balance conditions and subconditions across multiple trials and sessions.

    Balance a set of conditions across a number of trials. Each top-level
    condition will have an equal number of trials; if the conditions cannot
    be balanced perfectly (i.e. the number of trials is not a multiple of
    the number of conditions), an error is thrown.  Conditions will
    be as balanced as possible within each session.  Each conditions may
    also have sub-conditions, which are made to be as balanced as
    possible within each session. The order of sub-conditions are
    randomized within each session.

    Inputs
    ------
    conds : tuple
        Tuple of condition codes.  Each element must be a tuple
        containing one or more codes for sub-conditions.
    nTrials : int
        The total number of trials, across all sessions.
    nSessions : int
        The number of sessions.
    shuffleType : str : {'set'|'all'|'none'}
        Indicates how the order of conditions will be randomized within
        each session.  See balanceConditions for details.  shuffleType
        is only applied to the top-level conditions; the order of sub-
        conditions is always randomized within each session.

    Outputs
    -------
    expConds: tuple : [session][trial]
        Gives the trial type code for each trial in the experiment.

    Examples
    --------
    >>> conds = ((0, 1), ((0,0), (0,1), (1,0), (1,1)))
    >>> balanceNestedConditions(conds, 8, 4, 'none')
    [1, (1, 0), 0, (1, 1), 1, (0, 0), 0, (0, 1)]
    >>> balanceConditions(conds, 8, 4, 'all')
    [(0, 0), 1, 0, (0, 1), 1, (1, 0), 0, (1, 1)]
    """
    
    nConds = len(conds)
    nSubConds = [len(x) for x in conds]
    maxSubConds = numpy.max(nSubConds)
    minTrials = numpy.max(nSubConds) * nConds

    # input checks
    if ((nTrials * nSessions) % nConds) != 0:
        raise ValueError("Total number of trials must be a multiple of "
                         "%d, so all top-level conditions can be "
                         "balanced." % nConds)
    elif (nTrials % nConds) != 0:
        # redundant with above; leaving that because this check will
        # not be necessary if I improve the algorithm later
        raise ValueError("Number of trials must be a multiple of %d. " %
                         nConds)

    # warnings
    if (nTrials % minTrials) != 0:
        print "Warning: sub-conditions will not be perfectly balanced "
        print "within session."
    if ((nTrials * nSessions) % minTrials) != 0:
        print "Warning: sub-conditions will not be perfectly balanced "
        print "within experiment."

    # balance conditions and randomize the order as specified
    # [session][trial]
    allCondInds = balanceSessions(range(nConds), nTrials, nSessions,
                                  shuffleType)
    
    # balance the sub-conditions and randomize order
    # [cond][session][n], where n is the nth trial of the parent
    # condition
    allSubConds = []
    for i in range(nConds):
        subCondTrials = balanceSessions(conds[i], nTrials/nConds, nSessions,
                                        shuffleType='all')
        allSubConds.append(subCondTrials)

    expConds = []
    for i in range(nSessions):
        sessConds = []
        for j in range(nTrials):
            # get the index of this condition
            condInd = allCondInds[i][j]

            # get the full condition by taking the next sub-condition
            fullCond = allSubConds[condInd][i].pop(0)
            sessConds.append(fullCond)
        expConds.append(sessConds)
    return expConds

