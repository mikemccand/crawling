import pickle
import csv
import localconstants
from load_utr_matches import Event, Match

def main():
  for kid_name, utr_id in localconstants.UTR_IDS.items():
    events = pickle.load(open(f'/Users/mike/utrcache/{utr_id}.pk', 'rb'))

    rows = []
    rows.append(['Event Name',
                 'Event Date',
                 'Match Time',
                 'Player1 Name',
                 'Player1 UTR',
                 'Player2 Name',
                 'Player2 UTR',
                 'Player1 Set Scores',
                 'Player2 Set Scores',
                 'Winner Name'])

    for event in events:
      for match in event.matches:
        rows.append([event.name, event.date,
                     match.match_time,
                     match.player1_name, match.player1_utr.strip(), match.player2_name, match.player2_utr.strip(),
                     ' '.join(match.player1_set_scores), ' '.join(match.player2_set_scores), match.winner_name])

    with open(f'{kid_name}.csv', 'w', newline='') as f:
      writer = csv.writer(f, delimiter=',')
      for row in rows:
        writer.writerow(row)

if __name__ == '__main__':
    main()
