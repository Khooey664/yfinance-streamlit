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
    
# Fetch company decription using API
def fetch_company_desc(selected_company):
    try:
        company_info = yf.Ticker(selected_company)
        description = company_info.info['longBusinessSummary']
        return description
    except Exception as e:
        st.error(f"Error fetching description: {e}")
        return None

# Run Streamlit
def main():
    st.title("Stock Data Viewer")
    conn = connect_to_db()

    if conn:
        # Fetch list of unique company names from the database
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT ticker FROM skfinance")
        companies = [row[0] for row in cursor.fetchall()]
        
        # Create dropdown to select company
        selected_company = st.selectbox("Select Company", companies)

        # Display company description
        company_data = fetch_company_data(conn, selected_company)
        if company_data:
            description = fetch_company_desc(selected_company)
            if description:
                st.write(description)

            # Display data in Streamlit app
            df = pd.DataFrame(company_data, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
            st.write(f"### Most Recent Stock Data for {selected_company}")
            st.dataframe(df)

            plt.figure(figsize=(12, 6))
            plt.plot(df['Date'], df['Close'], marker='o', linestyle='-')
            plt.title(f"Stock Price Over Time for {selected_company}")
            plt.xlabel("Date")
            plt.ylabel("Closing Price")
            plt.xticks(rotation=45)
            st.pyplot(plt)
        else:
            st.warning("No data found in database, try another company.")

if __name__ == "__main__":
    main()