# app.py — WORKING VERSION WITHOUT AUTH (Add password later)
import streamlit as st
import pandas as pd
from PIL import Image
import os

st.set_page_config(page_title="Orascoptic Pricing Tool", layout="wide")

# Load data
@st.cache_data
def load_sheet(sheet_name):
    try:
        return pd.read_excel("Pricing Sheet for Development.xlsx", sheet_name=sheet_name, header=None)
    except Exception as e:
        st.error(f"Could not load {sheet_name}: {e}")
        return pd.DataFrame()

accessories_df = load_sheet("Accessories")
loupes_df = load_sheet("Loupes Only")
lights_df = load_sheet("Light Systems")
omni_df = load_sheet("Omni Optic")
school_df = load_sheet("School Bundles")

# Session state
if 'selection_list' not in st.session_state:
    st.session_state.selection_list = []
if 'totals' not in st.session_state:
    st.session_state.totals = {}
if 'bifocal_price' not in st.session_state:
    st.session_state.bifocal_price = 0
if 'discount' not in st.session_state:
    st.session_state.discount = 0

# Helpers
def format_price(price):
    try:
        return f"{float(price):,.2f}"
    except:
        return "N/A"

def parse_price_entry(entry):
    if mode == 'Accessories' and not accessories_df.empty:
        markets = [str(x) for x in accessories_df.iloc[2, 4:].dropna().tolist() if x != '']
        market = st.selectbox("Select Market", ['Select Market'] + markets)
        
        categories = [str(x) for x in accessories_df.iloc[4:, 0].dropna().astype(str).unique().tolist() if x != '']
        category = st.selectbox("Select Category", ['Select Category'] + categories)
        
        sub_categories = []
        if category != 'Select Category':
            sub_mask = accessories_df.iloc[:, 0] == category
            sub_categories = [str(x) for x in accessories_df.loc[sub_mask, 1].dropna().astype(str).unique().tolist() if x != '']
        sub_category = st.selectbox("Select Sub-Category", ['Select Sub-Category'] + sub_categories)
        
        descriptions = []
        if sub_category != 'Select Sub-Category':
            sub_mask = (accessories_df.iloc[:, 0] == category) & (accessories_df.iloc[:, 1] == sub_category)
            descriptions = [str(x) for x in accessories_df.loc[sub_mask, 3].dropna().astype(str).unique().tolist() if x != '']
        description = st.selectbox("Select Description", ['Select Description'] + descriptions)
        
        if all([market != 'Select Market', category != 'Select Category', sub_category != 'Select Sub-Category', description != 'Select Description']):
            market_col = list(accessories_df.iloc[2]).index(market) 
            row_mask = (accessories_df.iloc[:, 0] == category) & (accessories_df.iloc[:, 1] == sub_category) & (accessories_df.iloc[:, 3] == description)
            if row_mask.any():
                row_idx = row_mask.idxmax()
                price = accessories_df.at[row_idx, market_col]
                currency = accessories_df.at[3, market_col]
                part = accessories_df.at[row_idx, 2]
                contents = accessories_df.at[row_idx, -1] if pd.notna(accessories_df.at[row_idx, -1]) else ''
                price_text = f"Price: {format_price(price)} {currency}"
                part_text = f"Part Number: {part}"
                contents_text = f"Contents: {contents}"
    
    # Loupes Only Mode
    elif mode == 'Loupes Only' and not loupes_df.empty:
        markets = [str(x) for x in loupes_df.iloc[1, 2:].dropna().tolist() if x != '']
        market = st.selectbox("Select Market", ['Select Market'] + markets)
        
        telescopes = [str(x) for x in loupes_df.iloc[3:33, 0].dropna().astype(str).unique().tolist() if x != '']
        telescope = st.selectbox("Select Telescope", ['Select Telescope'] + telescopes)
        
        frames = []
        if telescope != 'Select Telescope':
            frame_mask = loupes_df.iloc[:, 0] == telescope
            frames = [str(x) for x in loupes_df.loc[frame_mask, 1].dropna().astype(str).unique().tolist() if x != '']
        frame = st.selectbox("Select Frame", ['Select Frame'] + frames)
        
        bifocal = st.checkbox("Bifocal?")
        st.session_state.bifocal_price = 100 if bifocal else 0  # Default from your code
        
        if all([market != 'Select Market', telescope != 'Select Telescope', frame != 'Select Frame']):
            market_col = list(loupes_df.iloc[1]).index(market) 
            row_mask = (loupes_df.iloc[:, 0] == telescope) & (loupes_df.iloc[:, 1] == frame)
            if row_mask.any():
                row_idx = row_mask.idxmax()
                price = loupes_df.at[row_idx, market_col]
                currency = loupes_df.at[2, market_col]
                price_text = f"Price: {format_price(price)} {currency}"
                if bifocal:
                    bifocal_price = loupes_df.at[row_idx, market_col + 2] if market_col + 2 < len(loupes_df.columns) else 100
                    st.session_state.bifocal_price = bifocal_price
                    price_text += f"\n+ Bifocal: {format_price(bifocal_price)} {currency}"
                part_text = f"Part Number: {loupes_df.at[row_idx, market_col + 1]}"
    
    # Light Systems Mode
    elif mode == 'Light Systems' and not lights_df.empty:
        markets = [str(x) for x in lights_df.iloc[2, 3:].dropna().tolist() if x != '']
        market = st.selectbox("Select Market", ['Select Market'] + markets)
        
        light_systems = [str(x) for x in lights_df.iloc[4:, 0].dropna().astype(str).unique().tolist() if x != '']
        light_system = st.selectbox("Select Light System", ['Select Light System'] + light_systems)
        
        descriptions = []
        if light_system != 'Select Light System':
            desc_mask = lights_df.iloc[:, 0] == light_system
            descriptions = [str(x) for x in lights_df.loc[desc_mask, 2].dropna().astype(str).unique().tolist() if x != '']
        description = st.selectbox("Select Description", ['Select Description'] + descriptions)
        
        if all([market != 'Select Market', light_system != 'Select Light System', description != 'Select Description']):
            market_col = list(lights_df.iloc[2]).index(market) 
            row_mask = (lights_df.iloc[:, 0] == light_system) & (lights_df.iloc[:, 2] == description)
            if row_mask.any():
                row_idx = row_mask.idxmax()
                price = lights_df.at[row_idx, market_col]
                currency = lights_df.at[3, market_col]
                part = lights_df.at[row_idx, 1]
                price_text = f"Price: {format_price(price)} {currency}"
                part_text = f"Part Number: {part}"
    
    # Omni Optic Mode (simplified)
    elif mode == 'Omni Optic' and not omni_df.empty:
        markets = [str(x) for x in omni_df.iloc[2, 2:13].dropna().tolist() if x != '']
        market = st.selectbox("Select Market", ['Select Market'] + markets)
        
        products = [str(x) for x in omni_df.iloc[4:16, 0].dropna().astype(str).unique().tolist() if x != '']
        product = st.selectbox("Select Product", ['Select Product'] + products)
        
        descriptions = []
        if product != 'Select Product':
            desc_mask = omni_df.iloc[:, 0] == product
            descriptions = [str(x) for x in omni
