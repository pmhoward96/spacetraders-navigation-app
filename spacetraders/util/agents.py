import json

import pandas as pd
import requests
import streamlit as st

import util.contracts as contracts
import util.ships as ships
import util.sqlite_functions as sqf


class Agent():
    """
    Class that represents an agent.
    
    Attributes:
    token (str): Token for the agent
    symbol (str): Symbol for the agent
    """
    def __init__(self, agentDic):
        """
        Initializes an Agent object.

        Parameters:
        agentDic (Dict): Dictionary containing agent information

        Returns:
        None
        """
        self.token = agentDic["token"]
        self.symbol = agentDic["symbol"]
    
    def get_agent_token(self):
        """
        Gets the token for the agent.

        Parameters:
        None

        Returns:
        str: Token for the agent
        """
        return self.token

    def get_agent_info(self):
        """
        Gets the agent information. By Hitting the API.
        
        Parameters:
        None
        
        Returns:
        Dict: Dictionary containing agent information
        """
        url = "https://api.spacetraders.io/v2/my/agent"
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(url, headers = headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            response = create_agent(self.symbol)
            self.token = response["token"]
            return response

    def get_contracts(self):
        """
        Gets the contracts for the agent. By Hitting the API.
        
        Parameters:
        None
        
        Returns:
        List of Contract: List of Contract objects
        """
        url = "https://api.spacetraders.io/v2/my/contracts"
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(url, headers = headers)
        if response.status_code == 200:
            contractList = []
            for c in response.json()["data"]:
                contractList.append(contracts.Contract(c))
                return contractList
        else:
            print(f"Error: {response.status_code} - {response.text}")
    
    def get_ships(self):
        """
        Gets the ships for the agent. By Hitting the API.
        
        Parameters:
        None
        
        Returns:
        List of Ship: List of Ship objects
        """
        url = "https://api.spacetraders.io/v2/my/ships"
        headers = headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(url, headers = headers)
        if response.status_code == 200:
            shipList = []
            for c in response.json()["data"]:
                shipList.append(ships.Ship(c))
            return shipList
        else:
            print(f"Error: {response.status_code} - {response.text}")
    

def load_all_agents():
    """
    Gets all agents from the SQLLite database.
    
    Parameters:
    None
    
    Returns:
    pd.DataFrame: DataFrame containing agent information
    """
    df = sqf.get_all_values("Agents")
    return df

def create_agent(agentSymbol):
    """
    Creates an agent by hitting the API.
    
    Parameters:
    agentSymbol (str): Symbol of the agent
    
    Returns:
    Dict: Dictionary containing agent information
    """
    url = 'https://api.spacetraders.io/v2/register'
    headers = {'Content-Type' : 'application/json'
               ,"Accept": "application/json"}
    params = {
        "symbol": agentSymbol
        ,"faction": "COSMIC"
        }
    response = requests.post(url, json = params).json()
    responseJson = response["data"]["agent"]
    responseJson["token"] = response["data"]["token"]
    sqf.update_agent_into(responseJson)
    return responseJson

def load_agent(agentSymbol):
    """
    Loads an agent from the SQLLite database.
    
    Parameters:
    agentSymbol (str): Symbol of the agent
    
    Returns:
    Agent: Agent object
    """
    conn = sqf.create_connection()
    cursor = conn.cursor()
    #Check if symbol in db
    query = "SELECT * from AGENTS WHERE symbol = " + "\'" + agentSymbol + "\'"
    agentDic = pd.read_sql_query(query, con = conn).to_dict('records')
    agent = Agent(agentDic[0])
    response = agent.get_agent_info()
    return agent