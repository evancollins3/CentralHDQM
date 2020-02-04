import tracemalloc

# Dumps the difference of memory usage before 
# and after executing the decorated function
def diff_mem_snapshots(func):
  if not tracemalloc.is_tracing():
    print('Starting tracemalloc!!!')
    tracemalloc.start()

  def wrapper():
    s1 = tracemalloc.take_snapshot()

    response = func()

    s2 = tracemalloc.take_snapshot()

    top_stats = s2.compare_to(s1, 'lineno')
    for stat in top_stats[:10]:
      print(stat)

    return response
  return wrapper
