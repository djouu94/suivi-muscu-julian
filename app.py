import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Initialize database
def init_database():
    conn = sqlite3.connect('workout.db')
    c = conn.cursor()
    
    # Create sessions table
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT NOT NULL,
                  type TEXT NOT NULL)''')
    
    # Create exercises table
    c.execute('''CREATE TABLE IF NOT EXISTS exercises
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id INTEGER,
                  name TEXT NOT NULL,
                  sets INTEGER,
                  reps INTEGER,
                  weight REAL,
                  FOREIGN KEY (session_id) REFERENCES sessions(id))''')
    
    conn.commit()
    conn.close()

def main():
    st.title("Suivi Muscu Julian")
    
    # Initialize database
    init_database()
    
    # Sidebar for navigation
    page = st.sidebar.selectbox("Navigation", ["Accueil", "Nouvel Entraînement", "Historique"])
    
    if page == "Accueil":
        st.write("Bienvenue dans votre application de suivi d'entraînement!")
        
    elif page == "Nouvel Entraînement":
        st.header("Nouvel Entraînement")
        # Add your workout tracking logic here
        
    elif page == "Historique":
        st.header("Historique des Entraînements")
        # Add your history viewing logic here

if __name__ == "__main__":
    main()
