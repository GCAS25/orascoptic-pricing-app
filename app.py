import streamlit as st
import pandas as pd
from PIL import Image
import streamlit_authenticator as stauth

# Page config for wide layout
st.set_page_config(page_title="Orascoptic Price Search", layout="wide")

# Authentication setup
names = ["User"]
usernames = ["orascoptic"]
passwords = ["Orascoptic2025!"]  # Change this to your preferred password
hashed_passwords = stauth.Hasher(passwords).generate()

authenticator = stauth.Authenticate(
    {"credentials": {"usernames": {usernames[0]: {"name": names[0], "password": hashed_passwords[0]}}}},
    "orascoptic_cookie",
    "random_signature_key_2025",
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login("Login to Orascoptic Pricing Tool", "main")

if authentication_status == False:
    st.error("Username/password is incorrect")
    st.stop()
elif authentication_status == None:
    st.warning("Please enter your username and password")
    st.stop()

# Load data from Excel (cached for speed)
@st.cache_data
def load_sheet(sheet_name):
    return pd.read_excel("Pricing Sheet for Development.xlsx", sheet_name=sheet_name, header=None)

# Load all sheets
accessories_df = load_sheet("Accessories")
loupes_df = load_sheet("Loupes Only")
lights_df = load_sheet("Light Systems")
omni_df = load_sheet("Omni Optic")
school_df = load_sheet("School Bundles")

# Session state initialization
if 'selection_list' not in st.session_state:
    st.session_state.selection_list = []
if 'totals' not in st.session_state:
    st.session_state.totals = {}
if 'bifocal_price' not in st.session_state:
    st.session_state.bifocal_price = 0
if 'discount' not in st.session_state:
    st.session_state.discount = 0

# Helper functions
def format_price(price):
    try:
        return f"{float(price):,.2f}"
    except:
        return str(price)

def parse_price_entry(entry):
    # Extract price and currency from entry
    import re
    match = re.search(r'(Price|Bundle):\s*([\d,]+\.?\d*)\s*(\S+)', entry)
    if match:
        return float(match.group(2).replace(',', '')), match.group(3)
    return 0, ''

def add_to_list(price_str, part_str, contents_str, mode):
    bifocal_add = 0
    if mode == 'Loupes Only' and st.session_state.bifocal_price > 0:
        bifocal_add = st.session_state.bifocal_price
        price_str += f"\n+ Bifocal: {format_price(bifocal_add)} {parse_price_entry(price_str)[1]}"
    
    full_entry = f"{price_str}\n{part_str}\n{contents_str}"
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
            if currency in totals:
                totals[currency] += price
            else:
                totals[currency] = price
    
    total_lines = []
    for currency, subtotal in totals.items():
        adjusted = subtotal - st.session_state.discount
        if adjusted < 0:
            adjusted = 0
        total_lines.append(f"{currency} {format_price(adjusted)}")
    
    return '\n'.join(total_lines) if total_lines else 'No items selected'

# Main UI
st.title("🦋 Orascoptic Accessories Price Search")
if os.path.exists("orascoptic_logo.png"):
    st.image(Image.open("orascoptic_logo.png"), width=250)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Product Selection")
    mode = st.selectbox("Select Mode:", ['Accessories', 'Loupes Only', 'Light Systems', 'Omni Optic', 'School Bundle'])
    
    price_text = ""
    part_text = ""
    contents_text = ""
    currency = ""
    
    # Accessories Mode
    if mode == 'Accessories':
        markets = accessories_df.iloc[2, 4:].dropna().astype(str).tolist()
        market = st.selectbox("Select Market", ['Select Market'] + markets)
        
        categories = accessories_df.iloc[4:, 0].dropna().astype(str).unique().tolist()
        category = st.selectbox("Select Category", ['Select Category'] + categories)
        
        sub_categories = []
        if category != 'Select Category':
            sub_mask = accessories_df.iloc[:, 0] == category
            sub_categories = accessories_df.loc[sub_mask, 1].dropna().astype(str).unique().tolist()
        sub_category = st.selectbox("Select Sub-Category", ['Select Sub-Category'] + sub_categories)
        
        descriptions = []
        if sub_category != 'Select Sub-Category':
            sub_mask = (accessories_df.iloc[:, 0] == category) & (accessories_df.iloc[:, 1] == sub_category)
            descriptions = accessories_df.loc[sub_mask, 3].dropna().astype(str).unique().tolist()
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
    elif mode == 'Loupes Only':
        markets = loupes_df.iloc[1, 2:].dropna().astype(str).tolist()
        market = st.selectbox("Select Market", ['Select Market'] + markets)
        
        telescopes = loupes_df.iloc[3:33, 0].dropna().astype(str).unique().tolist()
        telescope = st.selectbox("Select Telescope", ['Select Telescope'] + telescopes)
        
        frames = []
        if telescope != 'Select Telescope':
            frame_mask = loupes_df.iloc[:, 0] == telescope
            frames = loupes_df.loc[frame_mask, 1].dropna().astype(str).unique().tolist()
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
                part = loupes_df.at[row_idx, market_col + 1]
                price_text = f"Price: {format_price(price)} {currency}"
                if bifocal:
                    bifocal_price = loupes_df.at[row_idx, market_col + 2] if market_col + 2 < len(loupes_df.columns) else 100
                    st.session_state.bifocal_price = bifocal_price
                    price_text += f"\n+ Bifocal: {format_price(bifocal_price)} {currency}"
                part_text = f"Part Number: {part}"
    
    # Light Systems Mode (simplified example - extend similarly for others)
    elif mode == 'Light Systems':
        markets = lights_df.iloc[2, 3:].dropna().astype(str).tolist()
        market = st.selectbox("Select Market", ['Select Market'] + markets)
        
        light_systems = lights_df.iloc[4:, 0].dropna().astype(str).unique().tolist()
        light_system = st.selectbox("Select Light System", ['Select Light System'] + light_systems)
        
        descriptions = []
        if light_system != 'Select Light System':
            desc_mask = lights_df.iloc[:, 0] == light_system
            descriptions = lights_df.loc[desc_mask, 2].dropna().astype(str).unique().tolist()
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
    
    # Omni Optic and School Bundle (similar pattern - add full logic if needed; truncated for length)
    elif mode == 'Omni Optic':
        st.info("Omni Optic mode: Select product, description, market (logic similar to Accessories).")
        # Add full dropdowns/logic here as above
    elif mode == 'School Bundle':
        st.info("School Bundle mode: Select loupe, light, configuration (bundle pricing logic).")
        # Add full dropdowns/logic here as above
    
    # Display results
    if price_text:
        st.success(price_text)
    if part_text:
        st.info(part_text)
    if contents_text:
        st.caption(contents_text)
    
    if st.button("➕ Add to List", type="primary") and price_text:
        add_to_list(price_text, part_text, contents_text, mode)
        st.success("Added to list!")
    
    if st.button("🔄 Reset Selection"):
        pass  # Streamlit resets on rerun

with col2:
    st.subheader("🛒 Shopping List & Total")
    
    # List display
    st.text_area("Items:", value='\n\n'.join(st.session_state.selection_list), height=300, disabled=True)
    
    # Totals
    total_display = update_total_display()
    st.metric("Sub-Total", total_display)
    
    # Discount
    discount_input = st.number_input("💰 Optional Discount", min_value=0.0, step=10.0)
    if st.button("Apply Discount"):
        st.session_state.discount = discount_input
        st.session_state.selection_list.append(f"Discount: -{format_price(discount_input)}")
        st.rerun()
    
    if st.button("🗑️ Reset List"):
        st.session_state.selection_list = []
        st.session_state.totals = {}
        st.session_state.discount = 0
        st.rerun()

# Sidebar logout
authenticator.logout("🚪 Logout", "sidebar")
