import os

import sys
from ROOT import gROOT, gSystem

class ForkPool:
  def __init__(self, max_forks):
    self.max_forks = max_forks

  def map(self, function, iterable):
    for chunk in self.__chunks(iterable, self.max_forks):
      pids = []
      for i in chunk:
        pid = os.fork()
        if pid == 0:
          # We are in the child process
          try:
            # f = open(os.devnull, 'w')
            # sys.stdout = f
            # sys.stderr = f
            # gROOT.ProcessLine( "gErrorIgnoreLevel = 6001;")
            # gSystem.RedirectOutput("/dev/null", "a")

            function(i)
          finally:
            # This is needed to properly exit out of the fork
            os._exit(0)
        else:
          # We are in the parent process. pid refers to a child
          pids.append(pid)
      # join
      for i in pids:
        os.waitpid(i, 0)
        pids.remove

  # Returns a generator of n-sized chunks
  def __chunks(self, lst, n):
    chunk=[]
    for i in lst:
      if len(chunk) >= n:
        yield chunk
        chunk=[]
      chunk.append(i)
    yield chunk
