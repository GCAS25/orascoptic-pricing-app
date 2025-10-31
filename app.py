# app.py — FINAL: ALL FIXES, NO ERRORS

import streamlit as st
import pandas as pd
from PIL import Image
import os
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import re

st.set_page_config(page_title="Envista Pricing Tool", layout="wide")

# === LOAD CONFIG ===
try:
    with open('config.yaml', 'r') as file:
        config = yaml.load(file, Loader=SafeLoader)
    st.success("Config loaded successfully.")
except Exception as e:
    st.error(f"Config load failed: {e}")
    st.stop()

# === AUTHENTICATOR ===
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# === LOGIN IN MAIN (location='main' REQUIRED!) ===
name, authentication_status, username = authenticator.login('Login', location='main')

if authentication_status == False:
    st.error('Username/password is incorrect')
    st.stop()
elif authentication_status is None:
    st.warning('Please enter your username and password.')

    # === REGISTRATION ===
    try:
        if authenticator.register_user('Register', pre_authorization=True):
            st.success('User registered successfully')
            with open('config.yaml', 'w') as file:
                yaml.dump(config, file, default_flow_style=False)
    except Exception as e:
        st.error(f"Registration failed: {e}")
    st.stop()

# === DOMAIN CHECK ===
user_email = config['credentials']['usernames'][username]['email']
if not user_email.endswith('@envistaco.com'):
    st.error('Access denied: Only @envistaco.com emails allowed.')
    st.stop()

# === LOGOUT IN MAIN ===
authenticator.logout('Logout', 'main')

# === LOAD EXCEL SHEETS ===
@st.cache_data
def load_sheet(sheet_name):
    try:
        return pd.read_excel("Pricing Sheet for Development.xlsx", sheet_name=sheet_name, header=None)
    except Exception as e:
        st.error(f"Could not load {sheet_name}: {e}")
        return pd.DataFrame()

accessories_df = load_sheet("Accessories")
loupes_df = load_sheet("Loupes Only")  # FIXED: loupes_df

lights_df = load_sheet("Light Systems")
omni_df = load_sheet("Omni Optic")
school_df = load_sheet("School Bundles")

# === SESSION STATE ===
if 'selection_list' not in st.session_state:
    st.session_state.selection_list = []
if 'totals' not in st.session_state:
    st.session_state.totals = {}
if 'bifocal_price' not in st.session_state:
    st.session_state.bifocal_price = 0
if 'discount' not in st.session_state:
    st.session_state.discount = 0

# === HELPERS ===
def format_price(price):
    try:
        return f"{float(price):,.2f}"
    except:
        return "N/A"

def parse_price_entry(entry):
    match = re.search(r'(Price|Bundle):\s*([\d,]+\.?\d*)\s*(\S+)', entry)
    if match:
        return float(match.group(2).replace(',', '')), match.group(3)
    return 0, ''

def add_to_list(price_str, part_str, contents_str, mode):
    bifocal_add = 0
    if mode == 'Loupes Only' and st.session_state.bifocal_price > 0:
        bifocal_add = st.session_state.bifocal_price
        price_str += f"\n+ Bifocal: {format_price(bifocal_add)} {parse_price_entry(price_str)[1]}"

    full_entry = f"{price_str}\n{part_str}\n{contents_str}".strip()
    st.session_state.selection_list.append(full_entry)

    price, currency = parse_price_entry(price_str)
    total_price = price + bifocal_add
    if currency in st.session_state.totals:
        st.session_state.totals[currency] += total_price
    else:
        st.session_state.totals[currency] = total_price

def update_total_display():
    totals = {}
    for entry in st.session_state.selection_list:
        if entry.startswith('Discount:'):
            continue
        price, currency = parse_price_entry(entry)
        if price > 0:
            totals[currency] = totals.get(currency, 0) + price

    total_lines = []
    for currency, subtotal in totals.items():
        adjusted = subtotal - st.session_state.discount
        if adjusted < 0:
            adjusted = 0
        total_lines.append(f"{currency} {format_price(adjusted)}")

    return '\n'.join(total_lines) if total_lines else 'No items selected'

# === MAIN UI ===
st.title("Orascoptic Accessories Price Search")
if os.path.exists("orascoptic_logo.png"):
    st.image(Image.open("orascoptic_logo.png"), width=250)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Product Selection")
    mode = st.selectbox("Select Mode:", [
        'Accessories', 'Loupes Only', 'Light Systems', 'Omni Optic', 'School Bundle'
    ])

    price_text = part_text = contents_text = ""

    # === ACCESSORIES MODE ===
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
            desc_mask = (accessories_df.iloc[:, 0] == category) & (accessories_df.iloc[:, 1] == sub_category)
            descriptions = [str(x) for x in accessories_df.loc[desc_mask, 3].dropna().astype(str).unique().tolist() if x != '']
        description = st.selectbox("Select Description", ['Select Description'] + descriptions)

        if all([market != 'Select Market', category != 'Select Category',
                sub_category != 'Select Sub-Category', description != 'Select Description']):
            market_col = list(accessories_df.iloc[2]).index(market)
            row_mask = (accessories_df.iloc[:, 0] == category) & \
                       (accessories_df.iloc[:, 1] == sub_category) & \
                       (accessories_df.iloc[:, 3] == description)
            if row_mask.any():
                row_idx = row_mask.idxmax()
                price = accessories_df.at[row_idx, market_col]
                currency = accessories_df.at[3, market_col]
                part = accessories_df.at[row_idx, 2]
                contents = accessories_df.iat[row_idx, -1] if pd.notna(accessories_df.iat[row_idx, -1]) else ''
                price_text = f"Price: {format_price(price)} {currency}"
                part_text = f"Part Number: {part}"
                contents_text = f"Contents: {contents}"

    # === LOUPES ONLY MODE ===
    elif mode == 'Loupes Only' and not loupes_df.empty:  # FIXED: loupes_df

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
        st.session_state.bifocal_price = 100 if bifocal else 0

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

    # === LIGHT SYSTEMS MODE ===
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

    # === OMNI OPTIC MODE ===
    elif mode == 'Omni Optic' and not omni_df.empty:
        markets = [str(x) for x in omni_df.iloc[2, 2:13].dropna().tolist() if x != '']
        market = st.selectbox("Select Market", ['Select Market'] + markets)

        products = [str(x) for x in omni_df.iloc[4:16, 0].dropna().astype(str).unique().tolist() if x != '']
        product = st.selectbox("Select Product", ['Select Product'] + products)

        descriptions = []
        if product != 'Select Product':
            desc_mask = omni_df.iloc[:, 0] == product
            descriptions = [str(x) for x in omni_df.loc[desc_mask, 1].dropna().astype(str).unique().tolist() if x != '']
        description = st.selectbox("Select Description", ['Select Description'] + descriptions)

        if all([market != 'Select Market', product != 'Select Product', description != 'Select Description']):
            market_col = list(omni_df.iloc[2]).index(market)
            row_mask = (omni_df.iloc[:, 0] == product) & (omni_df.iloc[:, 1] == description)
            if row_mask.any():
                row_idx = row_mask.idxmax()
                price = omni_df.at[row_idx, market_col]
                currency = omni_df.at[3, market_col]
                price_text = f"Price: {format_price(price)} {currency}"
                part_text = "Part Number: N/A"

    # === SCHOOL BUNDLE MODE ===
    elif mode == 'School Bundle' and not school_df.empty:
        configs = [str(x) for x in school_df.iloc[1, 3:19].dropna().tolist() if x != '']
        config = st.selectbox("Select Configuration", ['Select Configuration'] + configs)

        loupes = [str(x) for x in school_df.iloc[6:45, 0].dropna().astype(str).unique().tolist() if x != '']
        loupe = st.selectbox("Select Loupe", ['Select Loupe'] + loupes)

        lights = []
        if loupe != 'Select Loupe':
            light_mask = school_df.iloc[:, 0] == loupe
            lights = [str(x) for x in school_df.loc[light_mask, 2].dropna().astype(str).unique().tolist() if x != '']
        light = st.selectbox("Select Light", ['Select Light'] + lights)

        if all([config != 'Select Configuration', loupe != 'Select Loupe', light != 'Select Light']):
            config_col = list(school_df.iloc[1]).index(config)
            row_mask = (school_df.iloc[:, 0] == loupe) & (school_df.iloc[:, 2] == light)
            if row_mask.any():
                row_idx = row_mask.idxmax()
                currency = school_df.at[2, config_col]
                bundle_price = school_df.at[row_idx, config_col + 3]
                price_text = f"Bundle: {format_price(bundle_price)} {currency}"
                part_text = f"Loupe: {format_price(school_df.at[row_idx, config_col])} {currency}\n" \
                           f"Light: {format_price(school_df.at[row_idx, config_col + 1])} {currency}\n" \
                           f"Discount: {format_price(school_df.at[row_idx, config_col + 2])} {currency}"
                contents_text = f"Loupe: {loupe}\nLight: {light}"

    # === DISPLAY RESULTS ===
    if price_text:
        st.success(price_text)
    if part_text:
        st.info(part_text)
    if contents_text:
        st.caption(contents_text)

    if st.button("Add to List", type="primary") and price_text:
        add_to_list(price_text, part_text, contents_text, mode)
        st.success("Added to list!")

with col2:
    st.subheader("Shopping List & Total")

    for item in st.session_state.selection_list:
        st.text(item)
        st.markdown("---")

    st.metric("Sub-Total", update_total_display())

    discount_input = st.number_input("Optional Discount", min_value=0.0, step=10.0)
    if st.button("Apply Discount"):  # FIXED: st.button(

        st.session_state.discount = discount_input
        st.session_state.selection_list.append(f"Discount: -{format_price(discount_input)}")
        st.rerun()

    if st.button("Reset List"):
        st.session_state.selection_list = []
        st.session_state.totals = {}
        st.session_state.discount = 0
        st.rerun()

st.sidebar.info(f"Logged in as: {name} ({user_email})")
