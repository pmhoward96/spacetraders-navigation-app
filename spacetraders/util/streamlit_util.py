import numpy as np
import pandas as pd
import streamlit as st


def dataframe_with_selections(df, columnsToHide, key):
    """
    Function that creates a dataframe with a selection column for the user to select rows.
    
    Parameters:
    df (pd.DataFrame): DataFrame to display
    columnsToHide (List): List of columns to hide
    key (str): Key for the streamlit component
    
    Returns:
    pd.DataFrame: DataFrame with selection column
    """
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Select", False)
    columnConfig = {"Select": st.column_config.CheckboxColumn(required=True)
    }
    for c in columnsToHide:
        columnConfig[c] = None
    # Get dataframe row-selections from user with st.data_editor
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        use_container_width=True,
        column_config=columnConfig,
        disabled=df.columns,
        key = key
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Select]
    return selected_rows.drop('Select', axis=1)

def sessionStateCallback(name):
    """
    Function that sets a session state variable to True.
    
    Parameters:
    name (str): Name of the session state variable
    
    Returns:
    None"""
    st.session_state[name] = True

def custom_object_list_to_df(object_list):
    """
    Function that converts a list of objects to a DataFrame. Used for custom objects to with nested dictionaries.

    Parameters:
    object_list (List): List of objects

    Returns:
    pd.DataFrame: DataFrame containing object information
    """
    attributeList = []
    for i in dir(object_list[0]):
        if "__" not in i and not callable(getattr(object_list[0], i)):
            attributeList.append(i)
    objectListDic = []
    for o in object_list:
        objectDic = {}
        for a in attributeList:
            objectDic[a] = getattr(o, a)
        objectListDic.append(objectDic)
    df = pd.DataFrame(objectListDic)
    return df
