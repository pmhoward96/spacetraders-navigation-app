import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import requests
import streamlit as st

import util.ships as ships
import util.sqlite_functions as sqf

# Waypoint types for Graphing
waypoint_types = ["PLANET", "GAS_GIANT", "MOON", "ORBITAL_STATION", "JUMP_GATE", "ASTEROID_FIELD", "ASTEROID", "ENGINEERED_ASTEROID", "ASTEROID_BASE", "NEBULA", "DEBRIS_FIELD", "GRAVITY_WELL", "ARTIFICIAL_GRAVITY_WELL", "FUEL_STATION"]

def chart_entire_universe_with_selections(df, ships = None):
    """
    Function that charts the entire universe with selections for ships.
    
    Parameters:
    df (pd.DataFrame): DataFrame containing universe information
    ships (List of Dicts): List of dicts containing ship information
    
    Returns:
    None"""
    fig = chart_system(df)
    st.plotly_chart(fig, key= 'galaxyFig')

def chart_with_pydeck(ships = None):
    """
    Function that charts the entire universe with selections for ships using Pydeck.
    
    Parameters:
    ships (List of Dicts): List of dicts containing ship information
    
    Returns:
    None"""
    df = sqf.get_all_values("Systems")
    if ships is not None:
        shipsDf = pd.DataFrame(ships)
        df = pd.concat([df, shipsDf])
    st.pydeck_chart(
         pdk.Deck(
              map_provider=None
            ,
         layers = [
               pdk.Layer("ScatterplotLayer",
                            pickable = True,
                            data = df,
                            get_position = "[y, x]",
                            color = ['type']
                            )
         ]
         )
    )
    
def chart_system(df):
    """
    Function that charts a system.
    
    Parameters:
    df (pd.DataFrame): DataFrame containing system information
    
    Returns:
    Plotly.Figure: Plotly figure
    """
    fig = px.scatter(
        df
        ,x = 'x'
        ,y= "y"
        ,color = 'type'
        ,symbol = 'type'
        ,hover_data=['symbol']
    )

    return fig

def search_system(token, system, traits=None):
    """
    Function that searches for a system for either all waypoints or waypoints with specific traits.
    
    Parameters:
    token (str): Token for the agent
    system (str): System to search
    traits (str): Traits to search for
    
    Returns:
    List of Dicts: List of dicts containing waypoint information
    """
    if traits == None:
        url = "https://api.spacetraders.io/v2/systems/" + system + "/waypoints"
    else:
         url = "https://api.spacetraders.io/v2/systems/" + system + "/waypoints?traits=" + traits
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers = headers)
    if response.status_code == 200:
        return response.json()['data']
    else:
            print(f"Error: {response.status_code} - {response.text}")
            return False

@st.cache_data
def get_all_waypoints(token):
    """
    Function that gets all waypoints. Data is cached by streamlit.
    
    Parameters:
    token (str): Token for the agent
    
    Returns:
    List of Dicts: List of dicts containing waypoint information"""
    page = 1
    all_waypoints = []
    while True:
        url = f"https://api.spacetraders.io/v2/systems?limit=20&page={page}"
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()['data']
            if not data:
                break
            all_waypoints.extend(data)
            page += 1
        else:
            print(f"Error: {response.status_code} - {response.text}")
            break
    return all_waypoints

def get_waypoint(token, systemSymbol, waypointSymbol):
    """ 
    Function that gets a waypoint.
    
    Parameters:
    token (str): Token for the agent
    systemSymbol (str): Symbol for the system
    waypointSymbol (str): Symbol for the waypoint
    
    Returns:
    Dict: Dictionary containing waypoint information"""
    url = f"https://api.spacetraders.io/v2/systems/{systemSymbol}/waypoints/{waypointSymbol}"
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers = headers)
    if response.status_code == 200:
        return response.json()
    else:
            print(f"Error: {response.status_code} - {response.text}")

def get_waypoints(token, system_symbol):
    """
    Function that gets all waypoints for a system.
    
    Parameters:
    token (str): Token for the agent
    system_symbol (str): Symbol for the system
    
    Returns:
    List of Dicts: List of dicts containing waypoint information
    """
    url = f"https://api.spacetraders.io/v2/systems/{system_symbol}/waypoints"
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['data']
    else:
        print(f"Error fetching waypoints: {response.status_code} - {response.text}")
        return []

def navigate_to_waypoint(token, ship_symbol, waypoint_symbol):
    """
    Function that navigates a ship to a waypoint.
    
    Parameters:
    token (str): Token for the agent
    ship_symbol (str): Symbol for the ship
    
    Returns:
    Dict: Dictionary containing waypoint information
    """
    url = f"https://api.spacetraders.io/v2/ships/{ship_symbol}/navigate"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    payload = {
        'waypointSymbol': waypoint_symbol
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error navigating to waypoint: {response.status_code} - {response.text}")
        return None

def refresh_systems(token):
    """
    Function that refreshes the systems table in the SQLite database.
    
    Parameters:
    token (str): Token for the agent
    
    Returns:
    None
    """
    conn = sqf.create_connection()
    cursor = conn.cursor()
    query = "DELETE FROM Systems"
    print(query)
    cursor.execute(query)
    sqf.close_connection(conn)

    url = "https://api.spacetraders.io/v2/systems"
    headers = {'Accept': "application/json"}
    data = []
    for i in range(1,20):
        response = (requests.get(url, headers).json()['data'])
        for j in response:
             data.append(j)

    df = pd.DataFrame(data)
    df = df.drop(columns = ['waypoints', 'factions'])
    df['waypoints'] = ''
    df['factions'] = ''
    sqf.insert_data("Systems", df)

def animated_system_plot(token, systemSymbol):
     """
     Function that creates an animated plot of a system with orbiting waypoints.
     
     Parameters:
     token (str): Token for the agent
     systemSymbol (str): Symbol for the system
     
     Returns:
     None"""
     if systemSymbol:
        waypoints = search_system(token, systemSymbol)
        # Number of frames for the animation
        num_frames = 100  # More frames for smoother animation

        # Time array for smoother animation
        t = np.linspace(0, 2 * np.pi, num_frames)

        # Prepare data for waypoints
        max_orbits = len(waypoints)
        waypoint_traces = []
        for i, wp in enumerate(waypoints, start=1):
            orbit_radius =  i * 10  # Radius for each orbit

            # Calculate positions over time for animation
            x_positions = orbit_radius * np.cos(t + i)  # Adding 'i' to offset starting positions
            y_positions = orbit_radius * np.sin(t + i)

            waypoint_traces.append({
                'x': x_positions,
                'y': y_positions,
                'name': wp['symbol'],
                'orbit_radius': orbit_radius
            })

        # Create frames for animation
        frames = []
        for frame_num in range(num_frames):
            frame_data = []

            # Add central star
            frame_data.append(go.Scatter(
                x=[0],
                y=[0],
                mode='markers+text',
                marker=dict(size=20, color='gold'),
                text=[systemSymbol],
                textposition="top center",
                showlegend=False
            ))

            # Add waypoints for this frame
            for wt in waypoint_traces:
                frame_data.append(go.Scatter(
                    x=[wt['x'][frame_num]],
                    y=[wt['y'][frame_num]],
                    mode='markers+text',
                    marker=dict(size=10, color='blue'),
                    textposition="top center",
                    showlegend=False
                ))

            frames.append(go.Frame(data=frame_data))

        # Initial data (first frame)
        initial_data = frames[0].data

        # Create the figure
        fig = go.Figure(
            data=initial_data,
            frames=frames,
            layout=go.Layout(
                xaxis=dict(range=[-max_orbits * 15, max_orbits * 15], autorange=False, zeroline=False, visible=False),
                yaxis=dict(range=[-max_orbits * 15, max_orbits * 15], autorange=False, zeroline=False, visible=False),
                plot_bgcolor="black",
                paper_bgcolor="black",
                height=600,
                width=600,
                title=f"System: {systemSymbol} with Orbiting Waypoints",
            )
        )

        # Add static orbit paths for each waypoint
        for wt in waypoint_traces:
            angle = np.linspace(0, 2 * np.pi, 100)
            fig.add_trace(go.Scatter(
                x=wt['orbit_radius'] * np.cos(angle),
                y=wt['orbit_radius'] * np.sin(angle),
                mode="lines",
                line=dict(color="lightgray", dash="dot"),
                showlegend=False
            ))

        # Set animation options to autoplay and loop
        fig.update_layout(
            autosize=True,
            updatemenus=[{
                "type": "buttons",
                "showactive": False,
                "buttons": [{
                    "label": "Play",
                    "method": "animate",
                    "args": [None,
                             {"frame": {"duration": 200, "redraw": True}, "fromcurrent": True, "mode": "immediate",
                              "loop": True}]
                }]
            }]
        )

        # Display the figure
        st.plotly_chart(fig, use_container_width=True)

def get_closest_systems(waypointsDf, ship, numSystems = None):
    """
    Function that gets the closest systems to a ship.
    
    Parameters:
    waypointsDf (pd.DataFrame): DataFrame containing waypoint information
    ship (Ship): Ship object
    numSystems (int): Number of systems to return
    
    Returns:
    pd.DataFrame: DataFrame containing closest systems
    """
    if numSystems == None:
        numSystems = 5
    shipX = ship.nav['route']['origin']['x']
    shipY = ship.nav['route']['origin']['y']
    waypointsDf['Distance'] = np.sqrt((waypointsDf['x'] - shipX)**2 + (waypointsDf['y'] - shipY)**2)
    waypointsDf = waypointsDf.sort_values(by = 'Distance')
    return waypointsDf.head(numSystems)

