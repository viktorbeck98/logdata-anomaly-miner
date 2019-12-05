"""This module defines a detector for unsorted timestamps."""

import os
from datetime import datetime

from aminer.events import EventSourceInterface
from aminer.input import AtomHandlerInterface
from aminer.analysis import CONFIG_KEY_LOG_LINE_PREFIX

class TimestampsUnsortedDetector(AtomHandlerInterface, EventSourceInterface):
  """This class creates events when unsorted timestamps are detected.
  This is useful mostly to detect algorithm malfunction or configuration
  errors, e.g. invalid timezone configuration."""

  def __init__(self, aminerConfig, anomalyEventHandlers, exitOnErrorFlag=False, outputLogLine=True):
    """Initialize the detector."""
    self.anomalyEventHandlers = anomalyEventHandlers
    self.lastTimestamp = 0
    self.exitOnErrorFlag = exitOnErrorFlag
    self.outputLogLine = outputLogLine
    self.aminerConfig = aminerConfig

  def receiveAtom(self, logAtom):
    """Receive on parsed atom and the information about the parser
    match.
    @param logAtom the parsed log atom
    @return True if this handler was really able to handle and
    process the match. Depending on this information, the caller
    may decide if it makes sense passing the parsed atom also
    to other handlers."""
    timestamp = logAtom.getTimestamp()
    if timestamp is None:
      return False
    if timestamp < self.lastTimestamp:
      if self.outputLogLine:
        originalLogLinePrefix = self.aminerConfig.configProperties.get(CONFIG_KEY_LOG_LINE_PREFIX)
        if originalLogLinePrefix is None:
          originalLogLinePrefix = ''
        sortedLogLines = [logAtom.parserMatch.matchElement.annotateMatch('')+os.linesep+ \
          originalLogLinePrefix+repr(logAtom.rawData)]
      else:
        sortedLogLines = [logAtom.parserMatch.matchElement.annotateMatch('')]
      for listener in self.anomalyEventHandlers:
        listener.receiveEvent('Analysis.%s' % self.__class__.__name__, \
            'Timestamp %s below %s' % \
            (datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"), \
            datetime.fromtimestamp(self.lastTimestamp).strftime("%Y-%m-%d %H:%M:%S")), \
            sortedLogLines, logAtom, self)
      if self.exitOnErrorFlag:
        import sys
        sys.exit(1)
    self.lastTimestamp = timestamp
    return True


  def whitelistEvent(self, eventType, sortedLogLines, eventData,
                     whitelistingData):
    """Whitelist an event generated by this source using the information
    emitted when generating the event.
    @return a message with information about whitelisting
    @throws Exception when whitelisting of this special event
    using given whitelistingData was not possible."""
    if eventType != 'Analysis.%s' % self.__class__.__name__:
      raise Exception('Event not from this source')
    raise Exception('No whitelisting for algorithm malfunction or configuration errors')
