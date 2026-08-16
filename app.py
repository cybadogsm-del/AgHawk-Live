import streamlit as st
import time
import hashlib
import sqlite3
import pandas as pd
from datetime import datetime

# ==========================================
# 1. SPLASH SCREEN & PAGE SETUP
# ==========================================
st.set_page_config(page_title="AgHawk", page_icon="🦅", layout="centered")

if "show_splash" not in st.session_state:
    st.session_state.show_splash = True

if st.session_state.show_splash:
    st.markdown("""
        <div style='text-align: center; margin-top: 30vh;'>
            <h1 style='font-size: 3.5em; margin-bottom: 0px;'>🦅 AgHawk</h1>
            <h3 style='font-style: italic; color: #4CAF50; margin-top: 5px;'>Every Detail in Real Time.</h3>
            <p style='margin-top: 20px; color: #888; font-size: 0.9em;'>System Initializing & Verifying Ledger...</p>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(2.0)
    st.session_state.show_splash = False
    st.rerun()

# ==========================================
# 2. DATABASE & TRUTH ENGINE
# ==========================================
conn = sqlite3.connect("aghawk_master.db", check_same_thread=False)
c = conn.cursor()

# Create our secure tables
c.execute('''CREATE TABLE IF NOT EXISTS users (pin TEXT PRIMARY KEY, name TEXT, role TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS works_orders (
             id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, operator TEXT, 
             field TEXT, equipment TEXT, hours REAL, gps_lat TEXT, gps_long TEXT, 
             entity_type TEXT, calculated_cost REAL, previous_hash TEXT, current_hash TEXT)''')
conn.commit()

# Add default users if the system is brand new
c.execute("SELECT * FROM users")
if not c.fetchall():
    c.execute("INSERT INTO users VALUES ('1234', 'Boss Mitchell', 'admin')")
    c.execute("INSERT INTO users VALUES ('5678', 'Tractor Driver', 'operator')")
    conn.commit()

def generate_hash(data, prev_hash):
    """The SHA-256 Truth Engine Math"""
    return hashlib.sha256(f"{data}{prev_hash}".encode()).hexdigest()

def get_last_hash():
    c.execute("SELECT current_hash FROM works_orders ORDER BY id DESC LIMIT 1")
    result = c.fetchone()
    return result[0] if result else "000000_START_OF_TIME"

# ==========================================
# 3. LOGIN SCREEN
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = ""
    st.session_state.user_role = ""

if not st.session_state.logged_in:
    st.title("🔒 AgHawk Secure Login")
    st.write("Please enter your 4-digit PIN to access the system.")
    
    pin_entry = st.text_input("Operator PIN:", type="password", max_chars=4)
    
    if st.button("Unlock System"):
        c.execute("SELECT name, role FROM users WHERE pin=?", (pin_entry,))
        user_data = c.fetchone()
        
        if user_data:
            st.session_state.logged_in = True
            st.session_state.current_user = user_data[0]
            st.session_state.user_role = user_data[1]
            st.rerun()
        else:
            st.error("❌ Incorrect PIN. Try again.")
    st.stop() # Stops the rest of the app from loading if not logged in

# ==========================================
# 4. MAIN APP (After Login)
# ==========================================
st.sidebar.title(f"👤 {st.session_state.current_user}")
st.sidebar.write(f"Access Level: {st.session_state.user_role.upper()}")

if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.rerun()

st.title("🚜 AgHawk Command Center")
st.write("Record your field work. Every entry is GPS stamped and locked by the Truth Engine.")

# --- JOB LOGGING FORM ---
with st.form("job_form"):
    st.subheader("Log A New Works Order")
    
    # 1. Location & Crop (including our premium turfs!)
    field_select = st.selectbox("Select Paddock/Field:", 
                                ["Front Paddock", "Hillside Block", "Stadium Pitch 1", "Create New Field..."])
    turf_variety = st.selectbox("Crop / Turf Variety:", 
                                ["Santa Anna Couch", "Sir Walter", "TifTuf", "Eureka", "Wheat", "Barley"])
    irrigation_used = st.checkbox("💧 Irrigation Used?")
    
    # 2. Equipment 
    equip_select = st.selectbox("Equipment Used:", 
                                ["John Deere Tractor", "Heavy Excavator (Wet Hire)", "Ride-on Cylinder Mower"])
    hours_worked = st.number_input("Hours Worked:", min_value=0.5, step=0.5)
    
    # 3. Two-Tier Pricing Logic
    st.markdown("---")
    entity_type = st.radio("Client Type (For Auto-Pricing):", ["Family Farm (Base Rate)", "Corporate Entity ($1150/mo Tier)"])
    
    # 4. The Fake GPS for our prototype
    st.info("📍 GPS Auto-Tracking (Simulated: Lat -37.8136, Long 144.9631)")
    
    submit_job = st.form_submit_button("🔒 Lock Job into Ledger")

# --- WHAT HAPPENS WHEN THEY CLICK SUBMIT ---
if submit_job:
    # Calculate fake cost based on tier
    hourly_rate = 150 if "Corporate" in entity_type else 85
    total_cost = hours_worked * hourly_rate
    
    # Do the Math for the Truth Engine!
    last_hash = get_last_hash()
    job_details = f"{st.session_state.current_user}-{field_select}-{equip_select}-{hours_worked}-{total_cost}"
    new_hash = generate_hash(job_details, last_hash)
    
    # Save it to the database
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''INSERT INTO works_orders 
                 (timestamp, operator, field, equipment, hours, gps_lat, gps_long, entity_type, calculated_cost, previous_hash, current_hash) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
              (timestamp, st.session_state.current_user, field_select, equip_select, hours_worked, "-37.8136", "144.9631", entity_type, total_cost, last_hash, new_hash))
    conn.commit()
    
    st.success("✅ Job Locked! The SHA-256 Truth Engine has secured this record.")

# --- ADMIN ONLY: VIEW THE LEDGER ---
if st.session_state.user_role == 'admin':
    st.markdown("---")
    st.subheader("🕵️‍♂️ Admin View: The Secure Ledger")
    st.write("Corporate Managers can view this immutable trail:")
    
    df = pd.read_sql_query("SELECT id, timestamp, operator, field, hours, calculated_cost, current_hash FROM works_orders", conn)
    if not df.empty:
        st.dataframe(df)
    else:
        st.write("No jobs logged yet!")
