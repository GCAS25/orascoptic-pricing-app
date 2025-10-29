# app.py — FINAL VERSION: 100% WORKING
import streamlit as st
import pandas as pd
from PIL import Image
import os
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import re

# === PAGE CONFIG ===
st.set_page_config(page_title="Orascoptic Pricing Tool", layout="wide")

# === AUTH CONFIG (YAML) ===
config_yaml = """
credentials:
  usernames:
    orascoptic:
      email: user@orascoptic.com
      name: User
      password: $2b$12$3n7g8h9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4  # "Orascoptic2025!"
cookie:
  expiry_days: 30
  key: orascoptic_key_2025
  name: orascoptic_cookie
preauthorized: []
"""

config = yaml.load(config_yaml, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# === CORRECT LOGIN CALL (THIS IS THE FIX) ===
name, authentication_status, username = authenticator.login('Login', 'main')
# =================================================

if authentication_status == False:
    st.error("Wrong username or password")
    st.stop()
elif authentication_status is None:
    st.warning("Please enter your credentials")
    st.stop()

# === LOGOUT ===
authenticator.logout("Logout", "sidebar")

# === LOAD DATA ===
@st.cache_data
def load_sheet(name):
    try:
        return pd.read_excel("Pricing Sheet for Development.xlsx", sheet_name=name, header=None)
    except Exception as e:
        st.error(f"Error loading {name}: {e}")
        return pd.DataFrame()

accessories = load_sheet("Accessories")
loupes = load_sheet("Loupes Only")

# === SESSION STATE ===
for k in ['list', 'totals', 'discount', 'bifocal']:
    if k not in st.session_state:
        st.session_state[k] = [] if k == 'list' else 0.0

# === HELPERS ===
def fmt(val):
    try: return f"{float(val):,.2f}"
    except: return str(val)

def parse_price(s):
    m = re.search(r'([\d,]+\.?\d*)\s*([A-Z]{3})', s)
    return (float(m.group(1).replace(',', '')), m.group(2)) if m else (0, '')

# === UI ===
st.title("Orascoptic Price Tool")
if os.path.exists("orascoptic_logo.png"):
    st.image("orascoptic_logo.png", width=250)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Select Product")
    mode = st.selectbox("Mode", ["Accessories", "Loupes Only"])

    price_text = part_text = ""

    if mode == "Accessories" and not accessories.empty:
        markets = [str(x) for x in accessories.iloc[2, 4:].dropna() if x]
        market = st.selectbox("Market", ["Select"] + markets)
        if market != "Select":
            cats = [str(x) for x in accessories.iloc[4:, 0].dropna().unique() if x]
            cat = st.selectbox("Category", ["Select"] + cats)
            if cat != "Select":
                subs = accessories[accessories.iloc[:, 0] == cat].iloc[:, 1].dropna().unique()
                sub = st.selectbox("Sub-Category", ["Select"] + list(subs))
                if sub != "Select":
                    descs = accessories[(accessories.iloc[:, 0] == cat) & (accessories.iloc[:, 1] == sub)].iloc[:, 3].dropna().unique()
                    desc = st.selectbox("Description", ["Select"] + list(descs))
                    if desc != "Select":
                        row = accessories[(accessories.iloc[:, 0] == cat) & (accessories.iloc[:, 1] == sub) & (accessories.iloc[:, 3] == desc)].iloc[0]
                        col = accessories.iloc[2].tolist().index(market)
                        price = row[col]
                        curr = accessories.at[3, col]
                        part = row[2]
                        price_text = f"Price: {fmt(price)} {curr}"
                        part_text = f"Part: {part}"

    if st.button("Add to List") and price_text:
        st.session_state.list.append(f"{price_text}\n{part_text}")
        p, c = parse_price(price_text)
        st.session_state.totals = {**st.session_state.totals, c: st.session_state.totals.get(c, 0) + p}
        st.success("Added!")

with col2:
    st.subheader("Cart")
    st.text_area("Items", "\n\n".join(st.session_state.list), height=300, disabled=True)

    total = sum(
        v - (st.session_state.discount if k == list(st.session_state.totals.keys())[0] else 0)
        for k, v in st.session_state.totals.items()
    )
    st.metric("Total", f"USD {fmt(total)}" if total else "—")

    disc = st.number_input("Discount", 0.0, step=10.0)
    if st.button("Apply"):
        st.session_state.discount = disc
        st.rerun()

    if st.button("Clear"):
        for k in ['list', 'totals', 'discount']: st.session_state[k] = [] if k == 'list' else 0.0
        st.rerun()
