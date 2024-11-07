import json
import time
from datetime import datetime

import pandas as pd
import requests
from prefect import flow, task

import util.agents as agents
import util.contracts as contracts
import util.nav as nav
import util.ships as ships
import util.sqlite_functions as sqf


def check_market(token, symbol, waypointSymbol):
    url = f'https://api.spacetraders.io/v2/systems/{symbol}/waypoints/{waypointSymbol}/market'
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers = headers)
    if response.status_code == 200:
        return response.json()['data']
    else:
            print(f"Error: {response.status_code} - {response.text}")


agent = agents.load_agent("PREY10")
ships = agent.get_ships()
#print(ships)
marketWapoints = []
for s in ships:
    waypoint = nav.get_waypoint(agent.get_agent_token(), s.nav['systemSymbol'], s.nav['waypointSymbol'])
    for t in waypoint['data']['traits']:
        if t['symbol'] == "MARKETPLACE":
            #print(f"Ship {s.symbol} is at a {t['name']}")
            marketWapoints.append([s.nav['systemSymbol'], s.nav['waypointSymbol']])
#print(marketWapoints)
transactions = []
tradeGoods = []
for mw in marketWapoints:
    marketData = (check_market(agent.get_agent_token(), mw[0], mw[1]))
    tradeGoodsSingle = marketData['tradeGoods']
    current_timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    for t in marketData['transactions']:
        transactions.append(t)
    for tg in marketData['tradeGoods']:
        tg['waypointSymbol'] = mw[1]
        tg['timestamp'] = current_timestamp
        tradeGoods.append(tg)  
transactionsDf = pd.DataFrame(transactions)
tradeGoodsDf = pd.DataFrame(tradeGoods)
print(transactionsDf)
print(tradeGoodsDf)

#sqf.insert_data("Market_Transactions", transactionsDf)
sqf.insert_data("Market_TradeGoods", tradeGoodsDf)