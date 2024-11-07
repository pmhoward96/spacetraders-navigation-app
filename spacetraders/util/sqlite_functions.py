import sqlite3

import pandas as pd

#Path to the database file
dbFile = "data/spaceTradersDb.db"

def create_connection():
    """
    Function that creates a connection to the SQLite database.
    
    Parameters:
    None
    
    Returns:
    sqlite3.Connection: Connection to the SQLite database
    """
    conn = None
    try:
        conn = sqlite3.connect(dbFile)
        #print(sqlite3.version)
    except Exception as e:
        print(e)
    finally:
        if conn:
            return conn
        
def close_connection(conn):
    """
    Function that closes the connection to the SQLite database.
    
    Parameters:
    conn (sqlite3.Connection): Connection to the SQLite database
    
    Returns:
    None
    """
    conn.close()

def create_table(tableName, columns):
    """
    Function that creates a table in the SQLite database.
    
    Parameters:
    tableName (str): Name of the table
    columns (List): List of lists containing column name and variable type
    
    Returns:
    None
    """
    conn = create_connection()
    cursor = conn.cursor()
    columnString = ""
    columnLen = len(columns)
    count = 0
    for i in columns:
        if count == columnLen - 1:
            columnString += i[0] + " " + i[1]
        else:
            columnString += i[0] + " " + i[1] + ", "
        count += 1
    query = "CREATE TABLE " + tableName + " (" + columnString + ");"
    print(columnString)
    try:
        cursor.execute(query)
    except Exception as e:
        print(e)
    close_connection(conn)

def insert_data(tableName, cvDf):
    """
    Function that inserts data into a table in the SQLite database.
    
    Parameters:
    tableName (str): Name of the table
    cvDf (pd.DataFrame): DataFrame containing the data to insert
    
    Returns:
    None"""
    print("Inserting data into " + tableName)
    conn = create_connection()
    cursor = conn.cursor()
    columns = cvDf.columns
    valuesList = cvDf.values.tolist()
    
    columnString = "("
    count = 0
    for c in columns:
        if count == len(columns) - 1:
            columnString += "?)"
        else:
            columnString += "?,"
        count += 1

    query = "INSERT INTO " + tableName + " VALUES " + columnString
    print(columns)
    print(valuesList)
    try:
        cursor.executemany(query, valuesList)
        conn.commit()
        close_connection(conn)
    except Exception as e:
        print(e)
        close_connection(conn)
        return e
    return True

def get_all_values(tableName):
    """
    Function that gets all values from a table in the SQLite database.
    
    Parameters:
    tableName (str): Name of the table
    
    Returns:
    pd.DataFrame: DataFrame containing all values from the table
    """
    conn = create_connection()
    cursor = conn.cursor()
    query = "SELECT * from " + tableName
    try:
        df = pd.read_sql_query(query, con = conn)

        close_connection(conn)
    except Exception as e:
        print(e)
        close_connection(conn)
        return e
    return df

def update_agent_into(agentDic):
    """
    Function that updates an agent into the SQLite database.
    
    Parameters:
    agentDic (Dict): Dictionary containing agent information
    
    Returns:
    None
    """
    conn = create_connection()
    cursor = conn.cursor()
    query = "SELECT * from AGENTS WHERE symbol = " + "\'" + agentDic['symbol'] + "\'"
    #Creates Query to get agent from database
    df = pd.read_sql_query(query, con = conn)
    #If agent not in database, insert
    if len(df) <= 0:
        columnString ="("
        valueString = "("
        count = 0
        for k in agentDic.keys():
            if count == len(agentDic) - 1:
                columnString += k + ")"
                valueString += "\'" + str(agentDic[k]) + "\'" + ")"
            else:
                columnString += k + ", "
                valueString += "\'" + str(agentDic[k]) + "\'"  + ", "
            count += 1
        query = "INSERT INTO AGENTS " + columnString + " VALUES " + valueString + (";")
        print(query)
        cursor.execute(query)
    #Else Update Agent Information
    else:
        query = "UPDATE AGENTS SET accountID = ?, headquarters = ?, token = ?"
        values = [agentDic["accountId"], agentDic["headquarters"], agentDic["token"]]
        cursor.execute(query, values)
    conn.commit()


