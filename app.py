import streamlit as st
import hashlib
import sqlite3

# ==========================================
# BRICK 1: THE VAULT (Database & Truth Engine)
# ==========================================
st.set_page_config(page_title="AgHawk OS - Brick 1", page_icon="🦅", layout="wide")

# Connect to Database
conn = sqlite3.connect("aghawk_master.db", check_same_thread=False)
c = conn.cursor()

# 1. Core Schema Setup
c.execute('''CREATE TABLE IF NOT EXISTS users (pin TEXT PRIMARY KEY, name TEXT, role TEXT, client_tier TEXT)''')

# Dynamic Crop Catalog implementing the system-wide user-addable rule
c.execute('''CREATE TABLE IF NOT EXISTS crop_catalog (
             id INTEGER PRIMARY KEY AUTOINCREMENT, 
             category TEXT, 
             crop_name TEXT UNIQUE, 
             is_custom INTEGER)''')

c.execute('''CREATE TABLE IF NOT EXISTS land_assets (
             id INTEGER PRIMARY KEY AUTOINCREMENT, 
             field_name TEXT, 
             category TEXT, 
             crop_name TEXT, 
             weather_status TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS machinery_assets (
             id INTEGER PRIMARY KEY, 
             equip_name TEXT, 
             engine_hours REAL, 
             status TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS works_orders (
             id INTEGER PRIMARY KEY AUTOINCREMENT, 
             operator TEXT, field TEXT, equipment TEXT, 
             client_name TEXT, client_tier TEXT, start_time TEXT, end_time TEXT, hours REAL, 
             calculated_cost REAL, status TEXT, previous_hash TEXT, current_hash TEXT)''')
conn.commit()

# 2. SHA-256 Truth Engine Cryptographic Functions
def generate_hash(data, prev_hash):
    return hashlib.sha256(f"{data}{prev_hash}".encode()).hexdigest()

def get_last_hash():
    c.execute("SELECT current_hash FROM works_orders WHERE status='LOCKED' ORDER BY id DESC LIMIT 1")
    result = c.fetchone()
    return result[0] if result else "000000_INITIAL_HASH"

# 3. Seed Initial Data & Australian Crop Sub-Databases
c.execute("SELECT * FROM users")
if not c.fetchall():
    # Users & Roles
    c.execute("INSERT INTO users VALUES ('1234', 'Boss Mitchell', 'admin', 'N/A')")
    c.execute("INSERT INTO users VALUES ('5678', 'Tractor Driver', 'operator', 'N/A')")
    c.execute("INSERT INTO users VALUES ('1111', 'Smith Family Farm', 'client', 'family')")
    c.execute("INSERT INTO users VALUES ('9999', 'MegaCorp Ag', 'client', 'corporate')")
    
    # Pre-seeded Australian Crops categorized under Broadacre & Market Garden
    default_crops = [
        # Broadacre Farming (includes Cereals, Turf, Horticulture, Potatoes, Grains)
        ('Broadacre Farming', 'Wheat (Cereal)', 0),
        ('Broadacre Farming', 'Barley (Cereal)', 0),
        ('Broadacre Farming', 'Oats (Cereal)', 0),
        ('Broadacre Farming', 'Sorghum (Cereal)', 0),
        ('Broadacre Farming', 'Canola', 0),
        ('Broadacre Farming', 'Potatoes (Commercial Broadacre)', 0),
        ('Broadacre Farming', 'Santa Anna Couch (Turf)', 0),
        ('Broadacre Farming', 'TifTuf Couch (Turf)', 0),
        ('Broadacre Farming', 'Sir Walter Buffalo (Turf)', 0),
        ('Broadacre Farming', 'Almonds (Orchard/Horticulture)', 0),
        ('Broadacre Farming', 'Wine Grapes (Horticulture)', 0),
        
        # Market Garden (Intensive Horticulture)
        ('Market Garden', 'Tomatoes', 0),
        ('Market Garden', 'Carrots', 0),
        ('Market Garden', 'Lettuce', 0),
        ('Market Garden', 'Onions', 0),
        ('Market Garden', 'Broccoli', 0),
        ('Market Garden', 'Cabbage', 0),
        ('Market Garden', 'Pumpkins', 0)
    ]
    c.executemany("INSERT OR IGNORE INTO crop_catalog (category, crop_name, is_custom) VALUES (?, ?, ?)", default_crops)
    
    # Default Assets
    c.execute("INSERT INTO land_assets (field_name, category, crop_name, weather_status) VALUES ('Front Paddock', 'Broadacre Farming', 'Santa Anna Couch (Turf)', 'Clear - Ready')")
    c.execute("INSERT INTO machinery_assets (equip_name, engine_hours, status) VALUES ('John Deere Tractor', 1200.5, 'Active')")
    conn.commit()

# --- BRICK 1 PREVIEW INTERFACE ---
st.title("🧱 Brick 1: The Vault & Crop Engine Inspection")
st.success("Database connected and pre-seeded with Australian agricultural taxonomy successfully.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🌾 Australian Crop Catalog (Sub-Databases)")
    df_crops = pd.read_sql_query("SELECT category, crop_name, CASE WHEN is_custom=1 THEN 'User Added' ELSE 'Default' END as Source FROM crop_catalog", conn) if 'pd' in globals() else None
    # Fallback view if pandas isn't explicitly imported in this snippet check:
    st.dataframe(pd.read_sql_query("SELECT category, crop_name, is_custom FROM crop_catalog", conn), use_container_width=True)

with col2:
    st.subheader("➕ System-Wide Crop Adder Test")
    with st.form("add_crop_form"):
        new_cat = st.selectbox("Category:", ["Broadacre Farming", "Market Garden"])
        new_crop_name = st.text_input("New Crop / Variety Name:")
        if st.form_submit_button("Add to System Catalog"):
            try:
                c.execute("INSERT INTO crop_catalog (category, crop_name, is_custom) VALUES (?, ?, 1)", (new_cat, new_crop_name))
                conn.commit()
                st.success(f"Successfully added '{new_crop_name}' system-wide!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("That crop already exists in the catalog.")
