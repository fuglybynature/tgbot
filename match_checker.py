# match_checker.py

import os
import requests

API_KEY = os.getenv("SPORTSDB_API_KEY")  # з .env

def get_next_matches(team_name):
    # Пошук команди по назві
    url_search = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/searchteams.php?t={team_name}"
    resp = requests.get(url_search)
    data = resp.json()
    if not data.get('teams'):
        return []

    team_id = data['teams'][0]['idTeam']

    # Отримання наступних матчів команди
    url_events = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventsnext.php?id={team_id}"
    resp = requests.get(url_events)
    data = resp.json()

    if not data or 'events' not in data or data['events'] is None:
        return []

    matches = []
    for event in data['events']:
        matches.append({
            'home': event['strHomeTeam'],
            'away': event['strAwayTeam'],
            'date': event['dateEvent'],
            'time': event['strTime'],
            'league': event['strLeague']
        })
    return matches
