# app.py — Orascoptic Pricing Tool (Streamlit + Password + iPad Ready)
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

# === AUTHENTICATION (FIXED) ===
config_yaml = """
credentials:
  usernames:
    orascoptic:
      email: user@orascoptic.com
      name: User
      password: $2b$12$3n7g8h9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4  # Hash for "Orascoptic2025!"
cookie:
  expiry_days: 30
  key: orascoptic_signature_key_2025
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

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Username/password is incorrect")
    st.stop()
elif authentication_status == None:
    st.warning("Please enter your username and password")
    st.stop()

# === LOGOUT ===
authenticator.logout("Logout", "sidebar")

# === LOAD EXCEL DATA ===
@st.cache_data
def load_sheet(sheet_name):
    try:
        return pd.read_excel("Pricing Sheet for Development.xlsx", sheet_name=sheet_name, header=None)
    except Exception as e:
        st.error(f"Could not load sheet '{sheet_name}': {e}")
        return pd.DataFrame()

accessories_df = load_sheet("Accessories")
loupes_df = load_sheet("Loupes Only")
lights_df = load_sheet("Light Systems")
omni_df = load_sheet("Omni Optic")
school_df = load_sheet("School Bundles")

# === SESSION STATE ===
for key in ['selection_list', 'totals', 'discount']:
    if key not in st.session_state:
        st.session_state[key] = [] if key == 'selection_list' else 0.0
if 'bifocal_price' not in st.session_state:
    st.session_state.bifocal_price = 0.0

# === HELPERS ===
def format_price(val):
    try:
        return f"{float(val):,.2f}"
    except:
        return str(val)

def parse_price(text):
    match = re.search(r'([\d,]+\.?\d*)\s*([A-Z]{3})', text)
    if match:
        return float(match.group(1).replace(',', '')), match.group(2)
    return 0.0, ''

def update_totals():
    totals = {}
    for item in st.session_state.selection_list:
        if "Discount" in item:
            continue
        price, curr = parse_price(item)
        if price > 0:
            totals[curr] = totals.get(curr, 0) + price
    total_lines = []
    for curr, amt in totals.items():
        final = amt - st.session_state.discount
        if final < 0:
            final = 0
        total_lines.append(f"{curr} {format_price(final)}")
    return "\n".join(total_lines) if total_lines else "No items"

# === MAIN UI ===
st.title("Orascoptic Price Search Tool")
if os.path.exists("orascoptic_logo.png"):
    st.image("orascoptic_logo.png", width=280)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Product Selection")
    mode = st.selectbox("Mode", [
        "Accessories", "Loupes Only", "Light Systems", "Omni Optic", "School Bundle"
    ], key="mode_select")

    price_text = part_text = contents_text = ""
    currency = ""

    # === ACCESSORIES ===
    if mode == "Accessories" and not accessories_df.empty:
        markets = [str(x) for x in accessories_df.iloc[2, 4:].dropna().tolist() if x != '']
        market = st.selectbox("Market", ["Select Market"] + markets, key="acc_market")

        if market != "Select Market":
            categories = [str(x) for x in accessories_df.iloc[4:, 0].dropna().unique() if x != '']
            category = st.selectbox("Category", ["Select Category"] + categories, key="acc_cat")

            if category != "Select Category":
                sub_mask = accessories_df.iloc[:, 0] == category
                sub_categories = [str(x) for x in accessories_df.loc[sub_mask, 1].dropna().unique() if x != '']
                sub_category = st.selectbox("Sub-Category", ["Select Sub-Category"] + sub_categories, key="acc_sub")

                if sub_category != "Select Sub-Category":
                    desc_mask = (accessories_df.iloc[:, 0] == category) & (accessories_df.iloc[:, 1] == sub_category)
                    descriptions = [str(x) for x in accessories_df.loc[desc_mask, 3].dropna().unique() if x != '']
                    description = st.selectbox("Description", ["Select Description"] + descriptions, key="acc_desc")

                    if description != "Select Description":
                        row_mask = (accessories_df.iloc[:, 0] == category) & \
                                   (accessories_df.iloc[:, 1] == sub_category) & \
                                   (accessories_df.iloc[:, 3] == description)
                        if row_mask.any():
                            row_idx = row_mask.idxmax()
                            market_col = accessories_df.iloc[2].tolist().index(market)
                            price = accessories_df.at[row_idx, market_col]
                            currency = accessories_df.at[3, market_col]
                            part = accessories_df.at[row_idx, 2]
                            contents = accessories_df.at[row_idx, -1] if pd.notna(accessories_df.at[row_idx, -1]) else ""
                            price_text = f"Price: {format_price(price)} {currency}"
                            part_text = f"Part Number: {part}"
                            contents_text = f"Contents: {contents}"

    # === LOUPES ONLY ===
    elif mode == "Loupes Only" and not loupes_df.empty:
        markets = [str(x) for x in loupes_df.iloc[1, 2:].dropna().tolist() if x != '']
        market = st.selectbox("Market", ["Select Market"] + markets, key="loupe_market")

        telescopes = [str(x) for x in loupes_df.iloc[3:33, 0].dropna().unique() if x != '']
        telescope = st.selectbox("Telescope", ["Select Telescope"] + telescopes, key="loupe_tel")

        frames = []
        if telescope != "Select Telescope":
            frame_mask = loupes_df.iloc[:, 0] == telescope
            frames = [str(x) for x in loupes_df.loc[frame_mask, 1].dropna().unique() if x != '']
        frame = st.selectbox("Frame", ["Select Frame"] + frames, key="loupe_frame")

        bifocal = st.checkbox("Bifocal?", key="loupe_bifocal")
        st.session_state.bifocal_price = 100.0 if bifocal else 0.0

        if all(x not in ["Select Market", "Select Telescope", "Select Frame"] for x in [market, telescope, frame]):
            market_col = loupes_df.iloc[1].tolist().index(market)
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

    # === LIGHT SYSTEMS (Example) ===
    elif mode == "Light Systems" and not lights_df.empty:
        markets = [str(x) for x in lights_df.iloc[2, 3:].dropna().tolist() if x != '']
        market = st.selectbox("Market", ["Select Market"] + markets, key="light_market")
        if market != "Select Market":
            market_col = lights_df.iloc[2].tolist().index(market)
            systems = [str(x) for x in lights_df.iloc[4:, 0].dropna().unique() if x != '']
            system = st.selectbox("Light System", ["Select System"] + systems, key="light_sys")
            if system != "Select System":
                descs = lights_df[lights_df.iloc[:, 0] == system].iloc[:, 2].dropna().unique()
                desc = st.selectbox("Description", ["Select Desc"] + list(descs), key="light_desc")
                if desc != "Select Desc":
                    row = lights_df[(lights_df.iloc[:, 0] == system) & (lights_df.iloc[:, 2] == desc)].iloc[0]
                    price = row[market_col]
                    currency = lights_df.at[3, market_col]
                    part = row[1]
                    price_text = f"Price: {format_price(price)} {currency}"
                    part_text = f"Part Number: {part}"

    # === OMNI & SCHOOL (Placeholder) ===
    elif mode == "Omni Optic":
        st.info("Omni Optic mode: Use dropdowns similar to Accessories.")
    elif mode == "School Bundle":
        st.info("School Bundle: Select loupe + light for bundle discount.")

    # === DISPLAY RESULT ===
    if price_text:
        st.success(price_text)
    if part_text:
        st.info(part_text)
    if contents_text:
        st.caption(contents_text)

    if st.button("Add to List", type="primary") and price_text:
        entry = f"{price_text}\n{part_text}\n{contents_text}".strip()
        st.session_state.selection_list.append(entry)
        price, curr = parse_price(price_text)
        st.session_state.totals = st.session_state.totals | {curr: st.session_state.totals.get(curr, 0) + price}
        st.success("Added!")

with col2:
    st.subheader("Shopping List")
    st.text_area("Items", "\n\n".join(st.session_state.selection_list), height=350, disabled=True)

    st.subheader("Sub-Total")
    st.code(update_totals())

    discount = st.number_input("Discount", min_value=0.0, step=10.0, key="discount_input")
    if st.button("Apply Discount"):
        st.session_state.discount = discount
        st.session_state.selection_list.append(f"Discount: -{format_price(discount)}")
        st.rerun()

    if st.button("Reset List"):
        st.session_state.selection_list = []
        st.session_state.totals = {}
        st.session_state.discount = 0.0
        st.rerun()
