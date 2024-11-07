# import sys
# import os
# # Add the directory containing the util module to the Python path
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
from prefect import flow, task, get_run_logger
from prefect.server.schemas.schedules import IntervalSchedule

import util.agents as agents
import util.contracts as contracts
import util.market as market
import util.nav as nav
import util.ships as ships
import util.sqlite_functions as sqf
import logging


@task
def load_agents():
    """
        Task that gets all agents.
    """
    logger = get_run_logger()
    logger.info("Loading agents.")
    df = agents.load_all_agents()
    return df

@task
def load_ships(agentsDf: pd.DataFrame):
    """
    Task that loads ships for all agents.

    Parameters:
    agentsDf (pd.DataFrame): Dataframe containing agent information

    Returns:
    List of Dicts: List of dicts containing agent, ships, and token
    """
    logger = get_run_logger()
    logger.info("Loading ships.")

    agentsSymbolList = agentsDf['symbol'].tolist()
    shipsList = []
    for a in agentsSymbolList:
        agent = agents.load_agent(a)
        shipsDic = {}
        shipsDic['Agent'] = agent.symbol
        shipsDic['Ships'] = agent.get_ships()
        shipsDic['Token'] = agent.get_agent_token()
        shipsList.append(shipsDic)
    return shipsList

@task
def get_market_waypoints(shipsList: list):
    """
    Task that checks if any ships are at a waypoint with a market

    Parameters:
    shipsList (list): List of ships to check if are at market waypoint.

    Returns:
    List of Dicts: List of dicts containing systemSymbol, waypointSymbol, and token of Market waypoints
    """
    logger = get_run_logger()
    logger.info("Getting market waypoints.")
    marketWapoints = []
    for agent in shipsList:
        for ship in agent['Ships']:
            waypoint = nav.get_waypoint(agent['Token'], ship.nav['systemSymbol'], ship.nav['waypointSymbol'])
            for t in waypoint['data']['traits']:
                if t['symbol'] == "MARKETPLACE":
                    marketDic = {'systemSymbol': ship.nav['systemSymbol'], 'waypointSymbol': ship.nav['waypointSymbol'], 'token': agent['Token']}
                    marketWapoints.append(marketDic)
    return marketWapoints

@task
def check_market(marketWaypoints: list):
    """
    Task that checks the market for various data points.

    Parameters:
    marketWaypoints (list): List of market waypoints.

    Returns:
    Dictionary: Dictionary containing transactions and trade goods as list of dicts
    """
    logger = get_run_logger()
    logger.info("Loading market data.")

    transactions = []
    tradeGoods = []
    for mw in marketWaypoints:
        marketData = market.check_market(mw['token'], mw['systemSymbol'], mw['waypointSymbol'])
        tradeGoodsSingle = marketData['tradeGoods']
        current_timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        for t in marketData['transactions']:
            transactions.append(t)
        for tg in marketData['tradeGoods']:
            tg['waypointSymbol'] = mw['waypointSymbol']
            tg['timestamp'] = current_timestamp
            tradeGoods.append(tg)
    data = {'transactions': transactions, 'tradeGoods': tradeGoods}
    return data

@task
def upload_transactions(transactions: list):
    """
    Task to put market transaction data into the sqlite db

    Parameters:
    transactions (list): Transaction data

    Returns:
    Boolean: True if successful, False if not
    """
    logger = get_run_logger()
    logger.info("Starting upload of transaction data.")
    transactionsDf = pd.DataFrame(transactions)
    return sqf.insert_data("Market_Transactions", transactionsDf)

@task
def upload_trade_goods(tradeGoods: list):
    """
    Task to put trade goods data into the sqlite db

    Parameters:
    tradeGoods (list): Trade Goods data

    Returns:
    dB: True if successful, False if not
    """
    logger = get_run_logger()
    logger.info("Starting upload of trade good data.")
    tradeGoodsDf = pd.DataFrame(tradeGoods)
    return sqf.insert_data("Market_TradeGoods", tradeGoodsDf)

@flow
def get_market_data():
    """
        Flow to get market data.
    """
    agentsDf = load_agents()
    shipsDic = load_ships(agentsDf)
    marketWaypoints = get_market_waypoints(shipsDic)
    marketData = check_market(marketWaypoints)
    # print(marketData['transactions'])
    # print(marketData['tradeGoods'])
    print("Upload transactions", upload_transactions(marketData['transactions']))
    print("Upload trade goods", upload_trade_goods(marketData['tradeGoods']))


if __name__ == '__main__':
    get_market_data.serve(name="get_market_data")