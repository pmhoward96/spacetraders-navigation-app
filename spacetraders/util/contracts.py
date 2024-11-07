import json

import pandas as pd
import requests
import streamlit as st

import util.sqlite_functions as sqf


class Contract():
    """
    Class that represents a contract.
    
    Attributes:
    id (str): Contract ID
    factionSymbol (str): Faction Symbol
    type (str): Type of contract
    terms (str): Terms of the contract
    accepted (bool): Whether the contract has been accepted
    fulfilled (bool): Whether the contract has been fulfilled
    expiration (str): Expiration of the contract
    deadlineToAccept (str): Deadline to accept the contract
    """

    def __init__(self, contractDic):
        """
        Initializes a Contract object.
        
        Parameters:
        contractDic (Dict): Dictionary containing contract information
        
        Returns:
        None
        """
        self.id = contractDic["id"]
        self.factionSymbol = contractDic["factionSymbol"]
        self.type = contractDic["type"]
        self.terms = contractDic["terms"]
        self.accepted = contractDic["accepted"]
        self.fulfilled = contractDic["fulfilled"]
        self.expiration = contractDic["expiration"]
        self.deadlineToAccept = contractDic["deadlineToAccept"]

    def print_contract(self):
        """
        Prints the contract information.
        
        Parameters:
        
        Returns:
        None
        """
        print(self.id)
        print(self.factionSymbol) 
        print(self.type) 
        print(self.terms) 
        print(self.accepted) 
        print(self.fulfilled)  
        print(self.expiration)  
        print(self.deadlineToAccept)
    
    def accept_contract(self, token):
        """
        Accepts the contract.
        
        Parameters:
        token (str): Token for the agent
        
        Returns:
        bool: Whether the contract was accepted
        """
        url = "https://api.spacetraders.io/v2/my/contracts/" + self.id + "/accept"
        headers = {'Authorization': f'Bearer {token}'
                   ,"Accept": "application/json"
                   ,"Content-Type": "application/json"}
        response = requests.post(url, headers = headers)
        if response.status_code == 200:
            self.accepted = True
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")

def get_contracts(token):
    """
    Gets the contracts for the agent. By Hitting the API.
    
    Parameters:
    token (str): Token for the agent
    
    Returns:
    List of Contract: List of Contract objects
    """
    url = 'https://api.spacetraders.io/v2/my/contracts'
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers = headers)
    if response.status_code == 200:
        accepted = True
        return response
    else:
        print(f"Error: {response.status_code} - {response.text}")

