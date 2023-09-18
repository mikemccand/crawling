import random
import copy

# TODO
#  - how do ties work?  what about the worst case (all trails same
#    length)?  combinatoric number of answers?  hmm, no, because we
#    only seek the sum(max(trails_across_days)), a single int result

def main():

  # generate random trails
  trails = []
  # nocommit
  # num_trails = random.randint(10, 300)

  # fixed seed for debugging
  rand = random.Random(17)

  num_trails = 10
  for i in range(num_trails):
    trails.append(rand.randint(1, 30))

  # pick number of days to pack trails into
  if False:
    while True:
      num_days = random.randint(10, 300)
      if num_days <= num_trails:
        break

  # nocommit
  num_days = 3

  #pack_days(trails, num_days)

  total_cost, answer = slow_pack_days(trails, num_days)

  l = []
  for day in answer:
    l.append(f'({" ".join([str(x) for x in day])})')
  print(f'{total_cost=} {"".join(l)}')


def cost(solution):
  return sum(max(day) for day in solution)

def slow_pack_days(trails, num_days, trail_upto=0, solution=None):

  if solution is None:
    # base case -- put first trail on first day!
    return slow_pack_days(trails, num_days, trail_upto+1, [[trails[0]]])
  elif trail_upto == len(trails):
    # end case
    if len(solution) == num_days:
      return cost(solution), copy.deepcopy(solution)
    else:
      # failed -- did not use up all days
      return None, None
  else:

    trail_length = trails[trail_upto]
    
    # option 1: stick current trail onto current day
    solution[-1].append(trail_length)
    total_cost1, solution1 = slow_pack_days(trails, num_days, trail_upto+1, solution)
    del solution[-1][-1]

    # option 2: make a new day here, if we are not maxed out on days yet
    if len(solution) < num_days:
      solution.append([trail_length])
      total_cost2, solution2 = slow_pack_days(trails, num_days, trail_upto+1, solution)
      del solution[-1]

      # TODO which way should the tie break go!
      if total_cost1 is None:
        # hmm both paths may be dead ends -- it's OK to return None, None
        # assert total_cost2 is not None
        return total_cost2, solution2
      elif total_cost2 is None:
        assert total_cost1 is not None
        return total_cost1, solution1
      elif total_cost1 < total_cost2:
        return total_cost1, solution1
      else:
        return total_cost2, solution2
    else:
      # new day not an option -- return same day score
      return total_cost1, solution1

def pack_days(trails, num_days):

  num_trails = len(trails)

  # sanity
  if num_trails == 0:
    raise RuntimeError('must have at least one trail; got 0')

  # sanity
  if num_days <= 0:
    raise RuntimeError(f'must have at least one day; got {num_days}')

  # sanity
  if num_days > num_trails:
    raise RuntimeError(f'number of days (got: {num_days}) must be <= number of trails (got: {num_trails})')

  print(f'{num_trails=} {num_days=}')
  
  # DP: 2D matrix -- X is each trail, Y is number of days we packed so far
  matrix = []

  for trail_upto in range(num_trails):

    print(f'{trail_upto=}')

    # we process this trail across the number of possible days so far
    trail_length = trails[trail_upto]

    # each entry in this will be the best we could do, up until the trails seen so far, by packed number of days
    by_num_days = []

    # at each entry in the matrix we store (min_so_far, current_day_max, start_new_day_here), or None for impossible cases

    for num_days_try in range(1, num_days+1):
      print(f'  {num_days_try=}')
      if num_days_try > 1+trail_upto:
        # no way to pack N trails into more than N days:
        by_num_days.append(None)
        print('    no')
        continue

      if trail_upto == 0 and num_days_try == 1:
        # base case -- given one trail and one day there is only one solution (walk that trail in that day):
        print('    new day (base case)')
        by_num_days.append((0, trail_length, True))
        continue

      assert trail_upto > 0

      # only two options for walking this trail: either do it on same day as prior day, or, start a new day
      # if we are not already at max days
      
      # 1) do this trail with the prior day

      prev = matrix[trail_upto-1][num_days_try-1]

      if prev is None:
        # there was no prior day -- only choice is to start a new day for this trail
        trail_same_day = None
      else:
        prev_total_cost, prev_day_max, was_new_day = prev
        trail_same_day = max(trail_length, prev_day_max)

      if num_days_try <= num_days and num_days_try > 1:
        # we can only spawn a new day if we are not already at the max number of days, and, we are at 2 or more days:
        # trail_new_day = trail_length + by_trail[trail_upto-1][num_days_try-2][0]
        trail_new_day = trail_length
      else:
        # impossible to start a new day: we've used up all days already
        trail_new_day = None

      # we are trying to minimize the sum of the max(trail_length) for each day:
      if trail_same_day is None:
        # must start a new day
        assert trail_new_day is not None
        by_num_days.append((prev_total_cost + prev_day_max, trail_new_day, True))
        print('    must new day (no prior day)')
      elif trail_new_day is None:
        # must append to previous day
        assert trail_same_day is not None
        by_num_days.append((prev_total_cost, trail_same_day, False))
        print('    must same day')
      elif prev_total_cost + trail_same_day < prev_total_cost + prev_day_max + trail_new_day:
        by_num_days.append((prev_total_cost, trail_same_day, False))
        print('    same day best')
      else:
        by_num_days.append((prev_total_cost + prev_day_max, trail_new_day, True))
        print('    new day best')

    # record our solution so far (up to this trail)
    matrix.append(by_num_days)

  print_matrix(trails, num_days, matrix)
  print_full_answer(trails, num_days, matrix)

  return matrix[num_trails-1][num_days-1]

def print_matrix(trails, num_days, matrix):
  num_trails = len(trails)

  print(f'\npack {num_trails} trails {trails} in {num_days} days')
  l = ['trail_length: ']
  for trail_length in trails:
    l.append(f' {trail_length:3d} ')
  l.append('\n')
  for num_days_try in range(1, num_days+1):
    l.append(f'    {num_days_try:3d} days: ')
    for trail_upto in range(num_trails):
      x = matrix[trail_upto][num_days_try-1]
      if x is None:
        l.append('     ')
      else:
        total_cost, day_cost, is_new_day = x
        s = f'{total_cost + day_cost}'
        if is_new_day:
          s += '*'
        else:
          s += ' '
        l.append(f'{s:>5s}')
    l.append('\n')

  print()
  print(''.join(l))

def print_full_answer(trails, num_days, matrix):

  num_trails = len(trails)

  trail_downto = num_trails-1
  day_downto = num_days - 1

  # backtrack in reverse
  day = []
  days = []

  last  = matrix[trail_downto][day_downto]
  best_score = last[0] + last[1]

  print('now backtrack')
  while trail_downto >= 0:

    start_new_day = matrix[trail_downto][day_downto][2]

    day.append(trails[trail_downto])
    
    if start_new_day:
      days.append(day)
      day = []
      day_downto -= 1

    trail_downto -= 1

  if len(days) != num_days:
    raise RuntimeError(f'saw {len(days)} days on backtrace, but expected {num_days}')

  days.reverse()
  for day in days:
    day.reverse()

  l = []
  score = 0
  for day in days:
    score += max(day)
    l.append(f'({" ".join(str(trail_length) for trail_length in day)})')

  assert score == best_score

  print(f'score {best_score}: {"".join(l)}')
                 
if __name__ == '__main__':
  main()

