import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
import json
import os
import sqlite3
import hashlib # Salasanan salaukseen
from datetime import date

# Tietokannan alustaminen. luo tiedoston jos sitä ei ole olemassa.
DB_FILE = "seuranta.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY,
                name TEXT,
                ticker TEXT,
                buy_price REAL,
                shares REAL,
                manual_price REAL,
                is_manual BOOLEAN,
                currency TEXT,
                buy_currency_rate REAL,
                current_currency_rate REAL,
                target_percentage REAL,
                portfolio_id INTEGER,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
            )
        """)
        conn.commit()

def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.rerun()

def login_user(username, password):
    hashed_password = hash_password(password)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ? AND password_hash = ?", (username, hashed_password))
        user = cursor.fetchone()
        if user:
            return user[0]
        return None

def register_user(username, password):
    hashed_password = hash_password(password)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

# UUSI: Käyttäjän todennustoiminnot
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    hashed_password = hash_password(password)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def login_user(username, password):
    hashed_password = hash_password(password)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ? AND password_hash = ?", (username, hashed_password))
        user = cursor.fetchone()
        if user:
            return user[0]
        return None

# UUSI: Tietokantapohjaiset tallennus- ja lataustoiminnot
def load_portfolios(user_id):
    portfolios = {}
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM portfolios WHERE user_id = ?", (user_id,))
        for portfolio_id, portfolio_name in cursor.fetchall():
            cursor.execute("SELECT name, ticker, buy_price, shares, manual_price, is_manual, currency, buy_currency_rate, current_currency_rate, target_percentage FROM assets WHERE portfolio_id = ?", (portfolio_id,))
            assets = [dict(zip(['name', 'ticker', 'buy_price', 'shares', 'manual_price', 'is_manual', 'currency', 'buy_currency_rate', 'current_currency_rate', 'target_percentage'], row)) for row in cursor.fetchall()]
            portfolios[portfolio_name] = assets
    return portfolios

def save_portfolios(user_id, portfolios):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        for portfolio_name, assets in portfolios.items():
            # Poista vanhat salkut ja kohteet
            cursor.execute("DELETE FROM portfolios WHERE user_id = ? AND name = ?", (user_id, portfolio_name))
            
            cursor.execute("INSERT INTO portfolios (name, user_id) VALUES (?, ?)", (portfolio_name, user_id))
            portfolio_id = cursor.lastrowid
            
            for asset in assets:
                cursor.execute("""
                    INSERT INTO assets (name, ticker, buy_price, shares, manual_price, is_manual, currency, buy_currency_rate, current_currency_rate, target_percentage, portfolio_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (asset['name'], asset['ticker'], asset['buy_price'], asset['shares'], asset['manual_price'], asset['is_manual'], asset['currency'], asset['buy_currency_rate'], asset['current_currency_rate'], asset['target_percentage'], portfolio_id))
        conn.commit()

# ... (Muu koodi pysyy samana, kuten get_stock_data, calculate_portfolio_metrics, display_portfolio_summary, create_pdf_report)
# HUOM: Varmista, että nämä funktiot eivät kutsu save_portfolios- tai load_portfolios-funktioita suoraan, vaan
# välittävät dataa `main`-funktion kautta.

# Koodisi lopussa:
if __name__ == "__main__":
    init_db() # Alusta tietokanta ennen main-funktion suoritusta
    main()

# PÄIVITETTY MAIN-FUNKTIO
def main():
    st.title("Sijoitussalkun seuranta 📊")

    # UUSI: Käyttäjän todennus
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_id = None
    
    if st.session_state.logged_in:
        # Käyttäjä on kirjautunut sisään, näytä sovelluksen toiminnot
        st.sidebar.button("Kirjaudu ulos", on_click=logout)
        
        # Ladataan salkut kirjautuneelle käyttäjälle
        portfolios = load_portfolios(st.session_state.user_id)
        
        # ... (Jäljellä oleva koodi pysyy lähes samana, mutta se on sijoitettu
        # TÄHÄN lohkoon. Muista kutsua uusia tallennus- ja latausfunktioita
        # käyttäen `st.session_state.user_id`-arvoa. )
        
    else:
        # Käyttäjä ei ole kirjautunut sisään, näytä kirjautumislomake
        st.sidebar.subheader("Kirjaudu sisään tai rekisteröidy")
        login_form = st.sidebar.form("login_form")
        username = login_form.text_input("Käyttäjätunnus")
        password = login_form.text_input("Salasana", type="password")
        col1, col2 = login_form.columns(2)
        
        with col1:
            if st.button("Kirjaudu sisään"):
                user_id = login_user(username, password)
                if user_id:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.success("Kirjautuminen onnistui!")
                    st.rerun()
                else:
                    st.error("Virheellinen käyttäjätunnus tai salasana")
        
        with col2:
            if st.button("Rekisteröidy"):
                if register_user(username, password):
                    st.success("Rekisteröinti onnistui! Voit nyt kirjautua sisään.")
                else:
                    st.error("Käyttäjätunnus on jo käytössä.")
