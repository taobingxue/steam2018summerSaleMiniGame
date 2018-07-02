#!/usr/bin/env python
# -*- coding: utf-8 -*- 
''' install requests: python -m pip install requests '''
import json, requests
import os, re, sys, time

MAX_TRY = 5
GAME_TIME = 120
LEVEL_SCORE = {1:585, 2:1170, 3:2340}
LANGUAGE = 'schinese'
def res_to_dict(res):
    return json.loads(res.text)["response"]

''' token '''
def ini_token():
    if os.path.exists('token'):
        return open('token').read()
    return read_token()

def read_token():
    token = input('input token：')
    while re.match('^[0-9a-f]{32}$',token) == None:
        token = input('invalid token，input token again：')
    open('token','w+').write(token)
    return token

''' auto play '''
def play():
    planets_info = get_planets_info()
    player_info = get_player_info()
    if ('active_planet' not in player_info):
        join_planet(list(planets_info.keys())[0])
        player_info = get_player_info()
    current_planet = player_info['active_planet']
    print('Currntly on planet ' + current_planet + ': ' + planets_info[current_planet]['state']['name'])
    
    while True:
        while True:
            valid_zones = get_valid_planet_zones(player_info['active_planet'])
            if (len(valid_zones) < 2):
                break
            join_zone(valid_zones[0]['zone_position'])
            count_down(GAME_TIME)
            report_score(LEVEL_SCORE[valid_zones[0]['difficulty']])
        leave_game(current_planet)
        
        planets_info = get_planets_info()
        p_keys = list(planets_info.keys())
        join_planet(p_keys[0] if p_keys[0] != current_planet else p_keys[1])
        player_info = get_player_info()
        current_planet = player_info['active_planet']
        print('Currntly on planet ' + current_planet + ': ' + planets_info[current_planet]['state']['name'])

def get_player_info():
    print('Get Player Info... ')
    params = {"access_token" : token}
    res = requests.post(r'https://community.steam-api.com/ITerritoryControlMinigameService/GetPlayerInfo/v0001/', data = params)
    return res_to_dict(res)

def get_planets_info():
    print('Get Planets Info... ')
    res = requests.get(r'https://community.steam-api.com/ITerritoryControlMinigameService/GetPlanets/v0001/?active_only=0&language=schinese')
    active_planets = {planet['id']:planet for planet in res_to_dict(res)['planets'] if ((not planet['state']['captured']) and planet['state']['active'])}
    if (not active_planets):
        print('No Planet Exists... ')
        sys.exit()
    return active_planets

def join_planet(planet_id):
    print('Join Planet id: ' + planet_id)
    params = {
        "access_token" : token,
        "id" : planet_id
    }
    res = requests.post(r'https://community.steam-api.com/ITerritoryControlMinigameService/JoinPlanet/v0001/', data = params)
    count = 1
    while res.status_code != 200 and count <= MAX_TRY:
        res = requests.post(r'https://community.steam-api.com/ITerritoryControlMinigameService/JoinPlanet/v0001/', data = params)
        count += 1
    if (res.status_code != 200):
        print('Fail To Join Planet... ')
        sys.exit()

def get_valid_planet_zones(planet_id):
    print('Get Planet Info of ' + planet_id + '...')
    res = requests.get(r'https://community.steam-api.com/ITerritoryControlMinigameService/GetPlanet/v0001/?id=' + planet_id + '&language=schinese')
    return [zone for zone in res_to_dict(res)['planets'][0]['zones'] if not zone['captured']]

def join_zone(zone_position):
    print('Start game at zone: ', zone_position)
    params = {
        "access_token" : token,
        "zone_position" : zone_position
    }
    res = requests.post(r'https://community.steam-api.com/ITerritoryControlMinigameService/JoinZone/v0001/', data = params)
    if (res.status_code != 200):
        print('Fail To Join Zone... ')
        sys.exit()

def count_down(t):
    for i in range(t, 0, -1):
        print(u'fighting... %ds left...' % i)
        time.sleep(1)

def report_score(score):
    print('Report score: ', score)
    params = {
        "access_token" : token,
        "language" : LANGUAGE,
        "score" : score
    }
    res = requests.post(r'https://community.steam-api.com/ITerritoryControlMinigameService/ReportScore/v0001/', data = params)
    if (res.status_code != 200):
        print('Fail To Report Score... ')
        sys.exit()
    
token = ini_token()
play()

