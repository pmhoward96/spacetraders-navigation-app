import json
import logging
import sqlite3
import sys

import pandas as pd
import requests
import streamlit as st

import util.agents as agents
import util.contracts as contracts
import util.market as market
import util.nav as nav
import util.ships as ships
import util.streamlit_util as stu

import plotly.graph_objects as go

st.set_page_config(
    page_title="SpaceTraders",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.title("Space Traders")

###################################################
#Streamlit Session State Keys 
agentKey = "agent"
if agentKey not in st.session_state:
    st.session_state[agentKey] = ""


with st.sidebar:
    st.title("Select Agent")
    #Get agents from SQLLite DB
    agentsDf = agents.load_all_agents()

    #Allow User to Select Agent, Load Agent, or Create Agent for Controlling Ships specfic to that agent
    agentsList = agentsDf.symbol.to_list()
    with st.expander("Agents"):
        agentSymbol = st.selectbox("Select Agent", agentsList, placeholder="Choose Agent", index=None)
        if st.button("Load Agent"):
            st.session_state[agentKey] = agents.load_agent(agentSymbol)
        with st.form("Create Agent"):
            agentSymbol = st.text_input("Create Agent")
            submitted = st.form_submit_button("Create")
            if submitted:
                agent = agents.create_agent(agentSymbol)
                st.session_state[agentKey] = agents.Agent(agent)

#Create Tabs for Ships, Contracts, and Market allowing for insight into each area
shipsTab, contractsTab, marketTab = st.tabs(["Ships", "Contracts", "Market"])

#Get all waypoints for the Entire Universe. Used for plotting and navigation
waypointsDf = nav.get_all_waypoints(st.session_state[agentKey].get_agent_token())

#Ship Tab for interactign with Ships
with shipsTab:
    st.header("Ships")

    #Get Ships for the Agent
    shipsList = st.session_state[agentKey].get_ships()
    shipSymbolList = []
    for s in shipsList:
        shipSymbolList.append({"Symbol": s.symbol, "ShipObject": s})
    shipsDf = pd.DataFrame(shipSymbolList)

    #For each ship, display the ship's information and interactions with Ships different systems
    col1, col2 = st.columns(2)

    #Basic Ship Information and Navigation to Key areas
    with col1:
        #Allow User to Select Ship to interact with
        selectedShips = st.selectbox("Ships", shipsDf)
        ship = shipsDf.loc[shipsDf["Symbol"] == selectedShips].to_dict('records')[0]['ShipObject']

        #Navigation within Ships System, Navigating within System requires different methods than System to System navigation
        st.markdown("Local Navigaton")
        st.markdown(ship.symbol)

        #Animated Plot of the System Ship is in
        nav.animated_system_plot(st.session_state[agentKey].token, ship.nav['systemSymbol'])
        #st.dataframe(pd.DataFrame([ship.nav]))

        #WORKTODO Find Shipyard in Ships System WORKTODO
        if st.button("Find Shipyard in Ships System"):
            shipyards = []

        #Session states to have nested buttons for finding markets and navigating to markets
        if "findMarket" not in st.session_state:
            st.session_state.findMarket = False
        if "navigateToMarket" not in st.session_state:
            st.session_state.navigateToMarket = False
        
        #Find Market in Ships System
        if st.button("Find Market in Ship's System") or st.session_state.findMarket:
            markets = []
            system_symbol = ship.nav['systemSymbol']
            # Fetch waypoints in the system
            waypoints = nav.get_waypoints(st.session_state[agentKey].token, system_symbol)
            # Filter waypoints with market trait
            # Due to the way the API is structured, the waypoints are nested in a list of dictionaries MARKETPLACE is the trait we are looking for
            for i in waypoints:
                for j in i['traits']:
                    print(i['symbol'], j['symbol'])
                    if j['symbol'] == "MARKETPLACE":
                        markets.append(i)
            #Set session state to True to allow for Streamlit to not close the button as soon as actions are taken within button
            st.session_state.findMarket = True
        
            #If markets are found, allow user to select market and navigate to market
            if markets:
                market_symbols = [market['symbol'] for market in markets]
                selected_market = st.selectbox("Select Market", market_symbols)
            
                if st.button("Navigate to Market") or st.session_state.navigateToMarket:
                    # Navigate the ship to the selected market
                    print("Navigate to Market", ship.navigate_to_waypoint(st.session_state[agentKey].token, waypoint_symbol = selected_market))
                        
            else:
                st.warning("No markets found in the current system.")
    
    #Ship Information and Interactions with Ship
    with col2:
        st.markdown("Ship Information")
        #Tabs for all Ship information
        registration, navi, crew, frame, reactor, engine, cooldown, modules, mounts, cargo, fuel = st.tabs(["Registration", "Nav", "Crew", "Frame", "Reactor", "Engine","Cooldown","Modules","Mounts","Cargo","Fuel"])
        
        #Registration Tab
        with registration:
            st.markdown("Registration")
            st.dataframe([ship.get_registration()])

        #Nav Tab
        with navi:
            #Streamlit Form to allowing segmenting of UI for Clean look
            #Allows to navigate to closes wapoints withing System
            with st.form("Navigate to Close Systems"):
                
                #Allows User to select number of Systems to Use - Probably outdated since we have selectbox to choose systems instead of dataframe
                numSystems = st.number_input("Number of Systems", min_value=1, max_value=10, value=1)
                closestSystemsDf = nav.get_closest_systems(pd.DataFrame(waypointsDf), ship, numSystems)
                
                #Combines Distance with Symbol for User to Select with relevatn information
                closestSystemsDf['description'] = closestSystemsDf.apply(lambda x: f"{x['symbol']} - {x['Distance']}", axis = 1)
                systemSelection = st.selectbox("Select System", closestSystemsDf['description'])
                systemSelectionSymbol = systemSelection.split(" - ")[0]
                
                #Get Waypoint Information for Selected System
                wayPointList = pd.DataFrame(nav.get_waypoints(st.session_state[agentKey].get_agent_token(), systemSelectionSymbol))
                
                #Select Waypoint to Navigate to
                wayPointSelect = st.selectbox("Select Waypoint", wayPointList)

                #When User Clicks Button, Ship will navigate to selected waypoint, checking if docked or in orbit first, this is needed to navigate to new system
                if st.form_submit_button("Navigate to Selected System"):
                    if ship.nav['status'] == "DOCKED":
                        ship.nav = ship.check_orbit(st.session_state[agentKey].token)
                    print("Ship Status", ship.nav)
                    if ship.nav['status'] == "IN_ORBIT":
                        print(ship.warp_to_new_system(st.session_state[agentKey].token, wayPointSelect))

#########TODO: Add Crew, Frame, Reactor, Engine, Cooldown, Modules, Mounts, Cargo, Fuel Tabs with relevant information          
        # with crew:
        #     st.markdown("Crew")
        #     for s in selectedShips:
        #         st.markdown(s)
        #         ship = shipsDf.loc[shipsDf["Symbol"] == s].to_dict('records')[0]
        #         st.dataframe(pd.DataFrame([ship["ShipObject"].crew]))
        # with frame:
        #     st.markdown("Frame")
        #     for s in selectedShips:
        #         st.markdown(s)
        #         ship = shipsDf.loc[shipsDf["Symbol"] == s].to_dict('records')[0]
        #         st.dataframe(pd.DataFrame([ship["ShipObject"].frame]))
        # with reactor:
        #     st.markdown("Reactor")
        #     for s in selectedShips:
        #         st.markdown(s)
        #         ship = shipsDf.loc[shipsDf["Symbol"] == s].to_dict('records')[0]
        #         st.dataframe(pd.DataFrame([ship["ShipObject"].reactor]))
        # with engine:
        #     st.markdown("Engine")
        #     for s in selectedShips:
        #         st.markdown(s)
        #         ship = shipsDf.loc[shipsDf["Symbol"] == s].to_dict('records')[0]
        #         st.dataframe(pd.DataFrame([ship["ShipObject"].engine]))
        # with cooldown:
        #     st.markdown("Cooldown")
        #     for s in selectedShips:
        #         st.markdown(s)
        #         ship = shipsDf.loc[shipsDf["Symbol"] == s].to_dict('records')[0]
        #         st.dataframe(pd.DataFrame([ship["ShipObject"].cooldown]))
        # with modules:
        #     st.markdown("Modules")
        #     st.dataframe(pd.DataFrame([ship.modules]))
        # with cargo:
        #     for s in selectedShips:
        #         st.markdown(s)
        #         ship = shipsDf.loc[shipsDf["Symbol"] == s].to_dict('records')[0]
        #         st.dataframe(pd.DataFrame(ship["ShipObject"].cargo.get_cargo()))
        # with mounts:
        #     st.markdown("Mounts")
        #     for s in selectedShips:
        #         st.markdown(s)
        #         ship = shipsDf.loc[shipsDf["Symbol"] == s].to_dict('records')[0]
        #         st.dataframe(pd.DataFrame([ship["ShipObject"].mounts]))
        # with fuel:
        #     st.markdown("Fuel")
        #     for s in selectedShips:
        #         st.markdown(s)
        #         ship = shipsDf.loc[shipsDf["Symbol"] == s].to_dict('records')[0]
        #         st.dataframe(pd.DataFrame([ship["ShipObject"].fuel]))
#Contracts Tab for interacting with Contracts
with contractsTab:
    st.header("Contracts")
    contractsList = st.session_state[agentKey].get_contracts()

    #Seperate types of contracts into different lists for display and interactions
    pendingContracts = []
    inProgressContracts = []
    finishedContracts = []
    for c in contractsList:
        if c.accepted:
            inProgressContracts.append(c)
        elif c.accepted and c.fulfilled:
            finishedContracts.append(c)
        else:
            pendingContracts.append(c)

    col1, col2 = st.columns([5,5])
    with col1:
        #Info about Pending Contracts
        st.markdown("**Pending**")
        for c in pendingContracts:
            with st.container(border=True):
                with st.expander(c.id):
                    pcol1, pcol2 = st.columns([5,5])
                    with pcol1:
                        st.markdown("**MetaData**")
                        st.markdown("Faction: " + c.factionSymbol)
                        st.markdown("Type: " + c.type)
                        st.markdown("Accepted?: " + str(c.accepted))
                        st.markdown("Fullfilled?: " + str(c.fulfilled))
                        st.markdown("Deadline to Accept: " + c.deadlineToAccept)
                        st.markdown("Expiration: " + c.expiration)
                    with pcol2:
                        st.markdown("**Terms**")
                        termsDic = c.terms
                        st.markdown("Upfront Payment: $" + str(termsDic["payment"]["onAccepted"]))
                        st.markdown("Final Payment: $" + str(termsDic["payment"]["onFulfilled"]))
                        st.markdown("**Goods**")
                        for g in termsDic["deliver"]:
                            st.markdown(g["tradeSymbol"])
                            #&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; adds spacing to markdown
                            st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Destination: " + g["destinationSymbol"])
                            st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Units Required: " + str(g["unitsRequired"]))
                    #Will Change State of Contract to Accepted
                    if st.button("Accept Contract", key=c.id):
                        accepted = c.accept_contract(st.session_state[agentKey].token)
                        st.rerun()

    #Info about in Progress Contracts                   
    with col2:
        st.markdown("In Progress")
        for c in inProgressContracts:
            with st.container(border=True):
                with st.expander(c.id):
                    pcol1, pcol2 = st.columns([5,5])
                    with pcol1:
                        st.markdown("**MetaData**")
                        st.markdown("Faction: " + c.factionSymbol)
                        st.markdown("Type: " + c.type)
                        st.markdown("Accepted?: " + str(c.accepted))
                        st.markdown("Fullfilled?: " + str(c.fulfilled))
                        st.markdown("Deadline to Accept: " + c.deadlineToAccept)
                        st.markdown("Expiration: " + c.expiration)
                    with pcol2:
                        st.markdown("**Terms**")
                        termsDic = c.terms
                        st.markdown("Upfront Payment: $" + str(termsDic["payment"]["onAccepted"]))
                        st.markdown("Final Payment: $" + str(termsDic["payment"]["onFulfilled"]))
                        st.markdown("**Goods**")
                        for g in termsDic["deliver"]:
                            st.markdown(g["tradeSymbol"])
                            #&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; adds spacing to markdown
                            st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Destination: " + g["destinationSymbol"])
                            st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Units Required: " + str(g["unitsRequired"]))

#Market Tab for interacting with Market
with marketTab:
    st.header("Market")
    print("Market Listings")
    #Get Transactions and Trade Goods from all ships stored in SQLLite DB
    transactionsDf = market.get_transactions()
    tradeGoodsDf = market.get_trade_goods()
    st.header("Market Transactions")

    #Allow User to Select Trade Good to view transactions for, also transofrm transactions to be sorted by timestamp for graphing
    tradeGoodSelecton = st.selectbox("Select Trade Good", transactionsDf['tradeSymbol'].unique(), index = 2)
    transactionsDf = transactionsDf[transactionsDf['tradeSymbol'] == tradeGoodSelecton]
    transactionsDf = transactionsDf.sort_values(by = 'timestamp').reset_index(drop = True)

    #Build Segments for Plotly Chart by comparing price per unit of each transaction over time
    segments = []
    color = 'green'

    for i in range(1, len(transactionsDf)):
        if transactionsDf['pricePerUnit'].to_list()[i] > transactionsDf['pricePerUnit'].to_list()[i - 1]:
            color = 'green'
        else:
            color = 'red'
    
        # Append segment
        segments.append(go.Scatter(
            x=transactionsDf['timestamp'].iloc[i-1:i+1],
            y=transactionsDf['pricePerUnit'].iloc[i-1:i+1],
            mode='lines',
            line=dict(color=color, width=3)
        ))


    fig = go.Figure(segments)
    

    # Update layout
    fig.update_layout(
        title='Market Transactions',
        xaxis_title='Timestamp',
        yaxis_title='Price Per Unit',
        xaxis_rangeslider_visible=False
    )

# Display the chart in Streamlit
    st.plotly_chart(fig)
    #st.dataframe(transactionsDf)
    st.dataframe(tradeGoodsDf)

#print("Ships Listing")
chartShipList = []
for s in shipsList:
     tempS = s.get_ships_for_charting(st.session_state[agentKey].get_agent_token())
     chartShipList.append(tempS)

#This is a chart of the enitre universe with all waypoints of All Systems
systemSelection = nav.chart_entire_universe_with_selections(waypointsDf)

