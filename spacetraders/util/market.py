import json

import pandas as pd
import requests
import streamlit as st

import util.contracts as contracts
import util.ships as ships
import util.sqlite_functions as sqf


def check_market(token, symbol, waypointSymbol):
    """
    Function that checks the market at a waypoint. Using symbol and wapointSymbol. Checks if the waypoint has a market happens outside of the fucntion.
    
    Parameters:
    token (str): Token for the agent
    symbol (str): Symbol for the system
    waypointSymbol (str): Symbol for the waypoint
    
    Returns:
    Dict: Dictionary containing market information
    """
    url = f'https://api.spacetraders.io/v2/systems/{symbol}/waypoints/{waypointSymbol}/market'
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers = headers)
    if response.status_code == 200:
        return response.json()['data']
    else:
            print(f"Error: {response.status_code} - {response.text}")

def get_transactions():
    """
    Function that gets all market transactions from SQLite database.

    Parameters:
    None

    Returns:
    pd.DataFrame: DataFrame containing all market transactions
    """
    transactions = sqf.get_all_values('Market_Transactions')
    return transactions

def get_trade_goods():
    """
    Function that gets all trade goods from SQLite database.
    
    Parameters:
    None
    
    Returns:
    pd.DataFrame: DataFrame containing all trade goods
    """
    trade_goods = sqf.get_all_values('Market_TradeGoods')
    return trade_goods