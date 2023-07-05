import pickle
import os
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup

re_whitespace = re.compile(r'\s+')

from localconstants import UTR_IDS, UTR_LOGIN_EMAIL, UTR_LOGIN_PASSWORD, UTR_CACHE_DIRECTORY

# TODO
#   - switch to headless
#   - run it with a proper UTR login so we get full UTR precision
#   - record country of each player too, and UTR
#   - is the UTR a snapshot at the time?  or is it the live UTR?

class Event:

  def __init__(self, name, date):
    self.name = name
    self.date = date
    self.matches = []

  def add_match(self, match):
    self.matches.append(match)

class Match:

  def __init__(self,
               match_time,
               player1_name, player1_utr, player1_set_scores,
               player2_name, player2_utr, player2_set_scores,
               winner_name):
    self.match_time = match_time
    self.player1_name = player1_name
    self.player1_utr = player1_utr
    self.player1_set_scores = player1_set_scores
    self.player2_name = player2_name
    self.player2_utr = player2_utr
    self.player2_set_scores = player2_set_scores
    self.winner_name = winner_name


driver = None
driver_wait = None

def get_driver():
  global driver
  global driver_wait

  # share one global driver so we only fire up Chrome & login once, and reuse

  if driver is None:
    options = Options()
    options.add_argument("--window-size=1920x1080")
    # options.add_argument("--verbose")
    # options.add_argument("--headless")

    driver = webdriver.Chrome(options=options, executable_path='/usr/local/bin/chromedriver')
    driver.get('https://app.universaltennis.com/login')

    driver_wait = WebDriverWait(driver, 30)

    driver_wait.until(EC.element_to_be_clickable((By.ID, 'emailInput'))).send_keys(UTR_EMAIL)

    # passwordInput = wait.until(EC.element_to_be_clickable((By.ID, 'passwordInput')))

    print('now find passwordInput')
    passwordInput = driver.find_element(By.ID, 'passwordInput')
    print('  got passwordInput')

    passwordInput.send_keys(UTR_LOGIN_PASSWORD)
    print('  done send_keys')

    passwordInput.submit()
    print('  done send_keys')

    print('now wait for login page to finish/load')
    driver_wait.until(EC.presence_of_element_located, (By.ID, 'myutr-app-wrapper'))

  return driver

def parse_profile_html(html):
  soup = BeautifulSoup(html, 'html.parser')

  # print(soup)

  all_events = []

  for event in soup.find_all(class_ = 'eventItem__eventItem__2Xpsd'):
    name = re_whitespace.sub(' ', event.find('div', class_='eventItem__eventName__6hntZ').text)
    date = re_whitespace.sub(' ', event.find('div', class_='eventItem__eventTime__3U8ST').text)
    event_instance = Event(name, date)
    all_events.append(event_instance)
    for match in event.find_all(class_ = 'utr-card'):

      # for some reason the match has data twice, once for "card view" and once for "list view":

      match = match.find('div', class_='list-view')

      match_time = match.find('div', class_='scorecard__header__2iDdF').text

      #print('\n\n')
      #print(match.prettify())
      # print(f'  NAME: {name.contents[0]} {name.contents[1]}')

      players = match.find_all('a', class_='player-name')
      utrs = match.find_all('div', class_='utr-container')

      scores_by_player = match.find_all('div', class_='scores-conatiner')

      if len(scores_by_player) != 2:
        raise RuntimeError(f'expected len(scores_by_player) == 2 but got {len(scores_by_player)}')

      player1_name = players[0].text
      player2_name = players[1].text

      player1_set_scores = scores_by_player[0].find_all('div', class_='score-item')
      player2_set_scores = scores_by_player[1].find_all('div', class_='score-item')

      player1_set_scores = [x.text for x in player1_set_scores]
      player2_set_scores = [x.text for x in player2_set_scores]

      if 'walkover' in scores_by_player[0].text:
        player1_set_scores = 'walkover'
      elif 'walkover' in scores_by_player[1].text:
        player2_set_scores = 'walkover'

      if 'winner' in utrs[0].prettify():
        winner_name = player1_name
      elif 'winner' in utrs[1].prettify():
        winner_name = player2_name
      else:
        match_status = match.find_all('div', class_='match-status-container')
        if len(match_status) != 1:
          raise RuntimeError(f'expected single match status but saw {len(match_status)}\nmatch: {match.prettify()}')
        if 'Tie' in match_status[0].text:
          winner_name = None
        else:
          raise RuntimeError(f'could not determine winner: {utrs}')

      player1_utr = utrs[0].text
      player2_utr = utrs[1].text

      event_instance.add_match(Match(match_time,
                                     player1_name, player1_utr, player1_set_scores,
                                     player2_name, player2_utr, player2_set_scores,
                                     winner_name))
  return all_events

def load_all_events(id):

  pk_cache_file = f'{UTR_CACHE_DIRECTORY}/{id}.pk'

  if not os.path.exists(pk_cache_file):

    html_cache_file = f'{UTR_CACHE_DIRECTORY}/{id}.html'

    if not os.path.exists(html_cache_file):

      profile_url = f'https://app.universaltennis.com/profiles/{id}'

      driver = get_driver()

      print(f'now load profile: {profile_url}')
      driver.get(profile_url)

      # must wait for AJAX load to fill in actual results
      driver_wait.until(EC.presence_of_element_located, (By.CLASS_NAME, 'eventItem__eventTime__3U8ST'))

      html = driver.page_source
      open(html_cache_file, 'w', encoding='utf8').write(html)
    else:
      print(f'  load from html cache {html_cache_file}')
      html = open(html_cache_file, encoding='utf8').read()

    print(f'now parse {len(html)} characters of HTML')

    all_events = parse_profile_html(html)

    open(pk_cache_file, 'wb').write(pickle.dumps(all_events))
  else:
    all_events = pickle.load(open(pk_cache_file, 'rb'))

  return all_events

def main():

  match_count = 0
  walkover_count = 0
  win_count = 0

  for name, id in UTR_IDS.items():

    print(f'\n\n{name} id={id}:')

    all_events = load_all_events(id)

    for event in all_events:
      print(f'\n\nEVENT: {event.name}\n  {event.date}')
      for match in event.matches:
        print(f'  match: {match.match_time} {match.player1_name} ({match.player1_utr}, set_scores: {match.player1_set_scores}) vs {match.player2_name} ({match.player2_utr} set scores: {match.player2_set_scores})')
        print(f'    winner: {match.winner_name}')
        match_count += 1
        if match.player1_name == name:
          if match.player1_set_scores == 'walkover':
            walkover_count += 1
        elif match.player2_name == name:
          if match.player2_set_scores == 'walkover':
            walkover_count += 1
        else:
          raise RuntimeError(f'saw a match without {name}?')

        if match.winner_name == name:
          win_count += 1

    print(f'\n{name}: {len(all_events)} events, {match_count} matches ({win_count} wins, {match_count - win_count - walkover_count} losses, {walkover_count} walkovers)')

if __name__ == '__main__':
  main()
