import json

import pandas as pd
import requests
import streamlit as st

import util.nav as nav
import util.sqlite_functions as sqf


class Cargo():
    """
    Class that represents cargo on a ship.

    Attributes:
    shipSymbol (str): Symbol for the ship
    capacity (int): Capacity of the cargo
    inventory (int): Inventory of the cargo
    units (str): Units of the cargo

    """
    def __init__(self, shipSymbol, cargoDic):
        """
        Initializes a Cargo object.
        
        Parameters:
        shipSymbol (str): Symbol for the ship
        cargoDic (Dict): Dictionary containing cargo information
        
        Returns:
        None
        """
        self.shipSymbol = shipSymbol
        self.capacity = cargoDic["capacity"]
        self.inventory = cargoDic["inventory"]
        self.units = cargoDic["units"]

    def get_cargo(self):
        """
        Gets the cargo information.
        
        Parameters:
        None
        
        Returns:
        List of Dicts: List of dictionaries containing cargo information
        """
        dic = {
            "Capacity": self.capacity
            ,"Inventory": self.inventory
            ,"Units": self.units
        }
        return [dic]

class Ship():
    """
    Class that represents a ship.
    
    Attributes:
    symbol (str): Symbol for the ship
    registration (str): Registration for the ship
    nav (Dict): Navigation information for the ship
    crew (int): Crew for the ship
    frame (str): Frame for the ship
    reactor (str): Reactor for the ship
    engine (str): Engine for the ship
    cooldown (int): Cooldown for the ship
    modules (List): Modules for the ship
    mounts (List): Mounts for the ship
    cargo (Cargo): Cargo for the ship
    fuel (int): Fuel for the ship
    
    """
    def __init__(self, shipDic):
        """
        Initializes a Ship object.
        
        Parameters:
        shipDic (Dict): Dictionary containing ship information
        
        Returns:
        None
        """

        self.symbol = shipDic['symbol']
        self.registration = shipDic['registration']
        self.nav = shipDic['nav']
        self.crew = shipDic['crew']
        self.frame = shipDic['frame']
        self.reactor = shipDic['reactor']
        self.engine = shipDic['engine']
        self.cooldown = shipDic['cooldown']
        self.modules = shipDic['modules']
        self.mounts = shipDic['mounts']
        self.cargo = Cargo(shipDic['symbol'], shipDic['cargo'])
        self.fuel = shipDic['fuel']

    def get_ships_for_charting(self, token):
        """ 
        Function that gets all ships for charting.
        
        Parameters:
        token (str): Token for the agent
        
        Returns:
        Dict: Dictionary containing ship information
        
        """
        waypoint = nav.get_waypoint(token, self.nav['systemSymbol'], self.nav['waypointSymbol'])
        shipDic = {
            "symbol" : self.symbol
            ,"systemSymbol" : self.nav['systemSymbol']
            ,"type" : "Ship"
            , "x": waypoint['data']['x']
            , "y": waypoint['data']['y']
            , "waypoints": self.nav['waypointSymbol']
            , "factions" : waypoint['data']['faction']['symbol']
        }
        return shipDic
    
    def get_registration(self):
        """
        Gets the registration for the ship.
        
        Parameters:
        None
        
        Returns:
        str: Registration for the ship
        """
        return self.registration
    
    def check_orbit(self, token):
        """ 
        Function that checks if the ship is in orbit. Ships must be in orbit to naviagte to a waypoint.
        
        Parameters:
        token (str): Token for the agent
        
        Returns:
        Dict: Dictionary containing ship information similar to nav, can be used to update the ship's nav information.
        
        """
        url = f"https://api.spacetraders.io/v2/my/ships/{self.symbol}/orbit"
        headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
        payload = ""
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            nav_data = response.json()['data']
            return nav_data
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
        
    def docking(self, token):
        """
        Function that docks the ship. Ships must be in orbit to dock.
        
        Parameters:
        token (str): Token for the agent
        
        Returns:
        Dict: Dictionary containing ship information similar to nav, can be used to update the ship's nav information.
        
        """
        url = f"https://api.spacetraders.io/v2/my/ships/{self.symbol}/dock"
        headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
        payload = ""
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            nav_data = response.json()['data']
            return nav_data
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
    
    def navigate_to_waypoint(self, token, waypoint_symbol):
        """
        Function that navigates the ship to a waypoint. Ships must be in orbit to navigate to a waypoint.
        
        Parameters:
        token (str): Token for the agent
        waypoint_symbol (str): Symbol for the waypoint
        
        Returns:
        Dict: Dictionary containing ship information similar to nav, can be used to update the ship's nav information.
        """
        url = f"https://api.spacetraders.io/v2/my/ships/{self.symbol}/navigate"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }

        payload = {
            'waypointSymbol': waypoint_symbol
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            st.success(f"Ship {self.symbol} is navigating to {waypoint_symbol}")
            return response.json()
        else:
            print(f"Error navigating to waypoint: {response.status_code} - {response.text}")
            return None
        
    def warp_to_new_system(self, token, waypointSymbol):
        """
        Function that warps the ship to a new system.
        
        Parameters:
        token (str): Token for the agent
        waypointSymbol (str): Symbol for the waypoint
        
        Returns:
        Dict: Dictionary containing ship information similar to nav, can be used to update the ship's nav information.
        """

        url = f"https://api.spacetraders.io/v2/ships/{self.symbol}/warp"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        payload = {
            'waypointSymbol': waypointSymbol
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error navigating to waypoint: {response.status_code} - {response.text}")
            return None

def find_shipyards(token, system):
    """
    Function that finds shipyards in a system.
    
    Parameters:
    token (str): Token for the agent
    system (str): Symbol for the system
    
    Returns:
    Dict: Dictionary containing shipyard information
    """
    data = nav.search_system(token, system, "SHIPYARD")
    if data['data']: 
        return data['data']
