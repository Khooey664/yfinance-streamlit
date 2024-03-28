import streamlit as st
import psycopg2
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to db
def connect_to_db():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    return conn

# Query and retrieve data
def fetch_company_data(conn, selected_company):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                date, open, high, low, close, adj_close, volume
            FROM 
                skfinance 
            WHERE 
                ticker = %s 
            ORDER BY
                date    
            """, (selected_company,))
        data = cursor.fetchall()
        return data
    except psycopg2.Error as e:
        st.error(f"Error fetching data from database: {e}")
        return None
    
def fetch_most_recent_company_data(conn, selected_company):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                date, open, high, low, close, adj_close, volume
            FROM 
                skfinance 
            WHERE 
                ticker = %s 
            ORDER BY
                date DESC
            LIMIT 1
            """, (selected_company,))
        data = cursor.fetchone()
        return [data]
    except psycopg2.Error as e:
        st.error(f"Error fetching data from database: {e}")
        return None

def fetch_company_data_date(conn, selected_company, start_date, end_date):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                date, open, high, low, close, adj_close, volume
            FROM 
                skfinance 
            WHERE 
                ticker = %s 
            AND
                date BETWEEN %s AND %s
            ORDER BY
                date    
            """, (selected_company, start_date, end_date))
        data = cursor.fetchall()
        return data
    except psycopg2.Error as e:
        st.error(f"Error fetching data from database: {e}")
        return None

# Fetch company decription using API
def fetch_company_desc(selected_company):
    try:
        company_info = yf.Ticker(selected_company)
        description = company_info.info['longBusinessSummary']
        return description
    except Exception as e:
        st.error(f"Error fetching description: {e}")
        return None

def plot_data(df, selected_column):
    plt.figure(figsize=(12, 6))
    plt.plot(df['Date'], df[selected_column], marker='o', linestyle='-')
    plt.title(f"{selected_column} Over time")
    plt.xlabel("Date")
    plt.ylabel(selected_column)
    plt.xticks(rotation=45)
    st.pyplot(plt)

# Run Streamlit
def main():
    st.title("Stock Data Viewer")
    st.divider()
    conn = connect_to_db()

    with st.sidebar:
        selected_tab = st.radio("Menu", ["Single stock analysis", "Stock comparison tool", "Date range analyser"])
    if selected_tab == "Single stock analysis":
        st.header("Stock Data")
        if conn:
            # Fetch list of unique company names from the database
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT ticker FROM skfinance")
            companies = [row[0] for row in cursor.fetchall()]
            
            # Create dropdown to select company
            selected_company = st.selectbox("Select Company", companies)

            selected_column = st.selectbox("Select data you would like to view", ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])

            # Display company description
            recent_data = fetch_most_recent_company_data(conn, selected_company)
            company_data = fetch_company_data(conn, selected_company)
            if company_data:
                description = fetch_company_desc(selected_company)
                if description:
                    st.write(description)

                # Display data in Streamlit app
                recent_df = pd.DataFrame(recent_data, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
                st.write(f"### Most Recent Stock Data for {selected_company}")
                st.dataframe(recent_df)

                df = pd.DataFrame(company_data, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
                plt.figure(figsize=(12, 6))
                plt.plot(df['Date'], df[selected_column].values, marker='o', linestyle='-')
                plt.title(f"{selected_column} Over time for {selected_company}")
                plt.xlabel("Date")
                plt.ylabel(selected_column)
                plt.xticks(rotation=45)
                st.pyplot(plt)
            else:
                st.warning("No data found in database, try another company.")
    
    elif selected_tab == "Stock comparison tool":
        # Fetch list of unique company names from the database
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT ticker FROM skfinance")
        companies = [row[0] for row in cursor.fetchall()]
        
        st.header("Stock comparison tool")
        st.write("Please select at least two companies to compare their data with")

        selected_company1 = st.selectbox("Select Company 1", companies)
        selected_company2 = st.selectbox("Select Company 2", companies)

        selected_column = st.selectbox("Select data you would like to view", ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])

        company_data1 = fetch_company_data(conn, selected_company1)
        company_data2 = fetch_company_data(conn, selected_company2)

        if company_data1 and company_data2:
            all_df1 = pd.DataFrame(company_data1, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
            all_df2 = pd.DataFrame(company_data2, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
            st.write(f"### All Stock Data for {selected_company1} and {selected_company2}")
            plt.figure(figsize=(12, 6))
            plt.plot(all_df1['Date'], all_df1[selected_column], marker='o', linestyle='-', label=selected_company1)
            plt.plot(all_df2['Date'], all_df2[selected_column], marker='o', linestyle='-', label=selected_company2)
            plt.title(f"{selected_column} Over time for {selected_company1} and {selected_company2}")
            plt.xlabel("Date")
            plt.ylabel(selected_column)
            plt.xticks(rotation=45)
            plt.legend()
            fig = plt.gcf()
            st.pyplot(fig)
        else:
            st.warning("No data found in database, try another company.")
    
    elif selected_tab == "Date range analyser":
        st.header("Select Dates Ranges")
        if conn:
            # Fetch list of unique company names from the database
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT ticker FROM skfinance")
            companies = [row[0] for row in cursor.fetchall()]
            
            # Create dropdown to select company
            selected_company = st.selectbox("Select Company", companies)

            # Date range selection
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")

            if start_date <= end_date:
                company_data = fetch_company_data_date(conn, selected_company, start_date, end_date)
                if company_data:
                    df = pd.DataFrame(company_data, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
                    st.write(f"### Stock Data for {selected_company} between {start_date} and {end_date}")
                    st.dataframe(df)

                    selected_column = st.selectbox("Select data you would like to view" , ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
                    plot_data(df, selected_column)
                else:
                    st.warning("No data found for the selected date range.")
            else:
                st.error("End Date must be after Start Date.")

if __name__ == "__main__":
    main()