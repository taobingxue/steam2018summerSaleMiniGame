#!/usr/bin/env python
# -*- coding: utf-8 -*- 
''' install requests: python -m pip install requests '''
import json, requests
import os, random, re, sys, time

MAX_TRY = 5
GAME_TIME = 120
LEVEL_SCORE = {1:585, 2:1170, 3:2360}
LANGUAGE = 'schinese'
RESELECT_GAP = 10

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
    target_planet = 'null'
    if ('active_planet' in player_info):
        target_planet = player_info['active_planet']
        print('Target planet %s: %s' % (target_planet, planets_info[target_planet]['state']['name']))
        leave_planet(target_planet)
    
    while True:
        boss_id = find_boss(list(planets_info.values()))
        if (boss_id in planets_info):
            boss_fight(planets_info[boss_id])
            planets_info = get_planets_info()
        
        tmp_planet = select_planet(list(planets_info.keys()), target_planet)
        join_planet(tmp_planet)
        print('Currntly on planet ' + tmp_planet + ': ' + planets_info[tmp_planet]['state']['name'])
        for i in range(RESELECT_GAP // 2):
            valid_zones = get_valid_planet_zones(tmp_planet)
            if (len(valid_zones) < 2):
                break
            fight_zone(valid_zones[0])
        leave_planet(tmp_planet)
        planets_info = get_planets_info()     
            

''' basic info '''
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

def leave_planet(planet_id):
    print('Leave Planet ' + planet_id)
    params = {
        "access_token" : token,
        "gameid" : planet_id
    }
    res = requests.post(r'https://community.steam-api.com/IMiniGameService/LeaveGame/v0001/', data = params)
    if (res.status_code != 200):
        print('Fail To Leave Planet... ')
        sys.exit()

def select_planet(planet_ids, target_planet):
    planet_ids.sort(key = lambda x: 0 - count_difficulties(x))
    if (count_difficulties(planet_ids[0]) > 0 or target_planet not in planet_ids):
        return planet_ids[0]
    else:
        return target_planet

def count_difficulties(planet_id):
    valid_zones = get_planet_info(planet_id)
    c3 = len([x for x in valid_zones if x['difficulty'] == 3])
    c2 = len([x for x in valid_zones if x['difficulty'] == 2])
    return c3 * 100 + c2

''' Fight on planet '''
def get_planet_info(planet_id):
    print('Get Planet Info of ' + planet_id + '...')
    res = requests.get(r'https://community.steam-api.com/ITerritoryControlMinigameService/GetPlanet/v0001/?id=' + planet_id + '&language=schinese')
    return [zone for zone in res_to_dict(res)['planets'][0]['zones'] if not zone['captured']]

''' get all valid zones in current planet with decreasing difficulty '''
def get_valid_planet_zones(planet_id):
    zones = get_planet_info(planet_id)
    zones.sort(key = lambda x: 0 - x['difficulty'])
    return zones

def fight_zone(zone):
    print('Start a game in zone: %s(difficulty: %d)' % (zone['zone_position'], zone['difficulty']))
    join_zone(zone['zone_position'])
    count_down(GAME_TIME)
    report_score(LEVEL_SCORE[zone['difficulty']])

def join_zone(zone_position):
    print('Join Zone: ', zone_position)
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
        print('fighting: %3ds left...  \r' % i, end = '')
        sys.stdout.flush()
        time.sleep(1)
    print('fighting:   0s left...  ')

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

''' boss '''
def find_boss(planets):
    print('find_boss: ')
    boss_planets = [planet['id'] for planet in planets if 'boss_zone_position' in planet['state']]
    print('boss_planet: ', boss_planets)
    return '-1' if not boss_planets else boss_planets[0]

def boss_fight(boss_planet):
    print('boss fight: ', boss_planet)
    join_planet(boss_planet['id'])
    boss_position = boss_planet['state']['boss_zone_position']
    
    while ([x for x in get_planet_info(boss_planet['id']) if (x['zone_position'] == boss_position) and x['boss_active']]):
        if not (join_boss_zone(boss_position)):
            break
        damage_boss()
    leave_planet(boss_planet['id'])

def join_boss_zone(zone_id):
    print('Join Boss Zone: ', zone_id)
    params = {
        "access_token" : token,
        "zone_position" : zone_id
    }
    res = requests.post(r'https://community.steam-api.com/ITerritoryControlMinigameService/JoinBossZone/v0001/', data = params)
    if (res.status_code != 200):
        print('Fail To Join Boss Zone... ')
        return False
    return True

def damage_boss():
    hp = 1
    while hp > 0:
        time.sleep(5)
        params = {
            "access_token" : token,
            "use_heal_ability" : 0,
            "damage_to_boss" : random.randint(22, 56),
            "damage_taken" : 0 if (random.randint(1, 7) > 1) else 5
        }
        res = requests.post(r'https://community.steam-api.com/ITerritoryControlMinigameService/ReportBossDamage/v0001/', data = params)
        if (res.status_code != 200):
            print('Fail To Report Boss Damage... ')
            return
        ''' this happened once, unreproducable, so put a check here to avoid possible crash '''
        if 'boss_status' not in res_to_dict(res):
            return
        boss = res_to_dict(res)['boss_status']
        hp = boss['boss_hp']
        print('Boss %.2f%% Left... ' % (hp / boss['boss_max_hp']), end = '')
        sys.stdout.flush()

token = ini_token()
play()
