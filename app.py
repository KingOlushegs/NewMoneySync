import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import os
from dotenv import load_dotenv
from omnisync.services import parse_retail_input_with_gemini, transcribe_audio_with_gemini

load_dotenv()
DB_NAME = "newmoneysync.db"

# --- DATABASE INITIALIZATION & AUTO-MIGRATION ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Core Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
            phone_number TEXT UNIQUE,
            password_hash TEXT,
            role TEXT DEFAULT 'standard',
            tier TEXT,
            entity_type TEXT,
            annual_turnover REAL,
            tax_bracket_rate REAL,
            coop_split_rate REAL,
            traffic_source TEXT,
            signup_date TEXT,
            cohort_week TEXT,
            primary_intent TEXT,
            onboarding_complete INTEGER DEFAULT 0
        )
    ''')
    
    # Check and add missing columns dynamically if an older database file exists
    cursor.execute("PRAGMA table_info(users)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    if "onboarding_complete" not in existing_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN onboarding_complete INTEGER DEFAULT 0")
    if "primary_intent" not in existing_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN primary_intent TEXT")
    if "coop_split_rate" not in existing_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN coop_split_rate REAL DEFAULT 5.0")
    if "tax_bracket_rate" not in existing_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN tax_bracket_rate REAL DEFAULT 7.5")
    if "phone_number" not in existing_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
    if "password_hash" not in existing_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    if "role" not in existing_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'standard'")

    # Invoices Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            client_name TEXT,
            amount REAL,
            asset_type TEXT,
            status TEXT,
            payment_tx_hash TEXT,
            created_at TEXT
        )
    ''')

    # Telemetry Events Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_name TEXT,
            timestamp TEXT,
            cohort_week TEXT
        )
    ''')

    # Cooperative Members Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cooperative_members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            member_name TEXT,
            email TEXT,
            department TEXT,
            monthly_contrib REAL,
            joined_at TEXT
        )
    ''')

    # Cooperative Ledger Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cooperative_ledger (
            ledger_id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT,
            member_id INTEGER,
            amount REAL,
            reference TEXT,
            timestamp TEXT,
            status TEXT
        )
    ''')

    # Payroll Directory Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payroll_directory (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            role TEXT,
            payout_rail TEXT,
            salary_amount REAL,
            created_at TEXT
        )
    ''')

    # Payroll History & Accounting Log Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payroll_history (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            run_date TEXT,
            recipient_count INTEGER,
            total_amount REAL,
            currency_summary TEXT,
            status TEXT
        )
    ''')

    # --- OMNISYNC RETAIL MODULE TABLES ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS omnisync_products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            category TEXT,
            cost_price REAL NOT NULL,
            selling_price REAL NOT NULL,
            created_at TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS omnisync_inventory (
            inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity_on_hand INTEGER NOT NULL DEFAULT 0,
            low_stock_threshold INTEGER DEFAULT 5,
            updated_at TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS omnisync_sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity_sold INTEGER,
            total_revenue REAL,
            total_cost REAL,
            net_profit REAL,
            created_at TEXT
        )
    ''')

    # Auto-seed Developer Account from Environment Variables
    dev_phone = os.getenv("DEV_PHONE", "07053723614")
    dev_pass = os.getenv("DEV_PASSWORD", "dadadatatada")
    
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, email, phone_number, password_hash, role, onboarding_complete)
        VALUES ('Lead Developer', 'oolushegs@yahoo.com', ?, ?, 'developer', 1)
    """, (dev_phone, dev_pass))

    conn.commit()
    conn.close()

init_db()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="NewMoneySync | Intelligent B2B & Cooperative Ledger",
    page_icon="💸",
    layout="wide"
)

# --- CLEAN FINTECH UI WITH SECURE SKY-BLUE ONLY DYNAMIC GRADIENTS ---
st.markdown("""
<style>
    @keyframes skyBlueShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    @keyframes skylinePan {
        0% { background-position: 0% bottom; }
        100% { background-position: 100% bottom; }
    }

    .stApp {
        background: linear-gradient(135deg, #BAE6FD, #38BDF8, #0EA5E9, #0284C7);
        background-size: 300% 300%;
        animation: skyBlueShift 25s ease infinite;
        color: #0F172A;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {
        background: 
            linear-gradient(180deg, #7DD3FC 0%, #38BDF8 50%, #0284C7 100%),
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 200' preserveAspectRatio='none'%3E%3Cpath d='M0,200 L0,150 L30,150 L30,120 L50,120 L50,200 L80,200 L80,90 L120,90 L120,200 L150,200 L150,60 L200,60 L200,200 L240,200 L240,110 L270,110 L270,200 L320,200 L320,40 L380,40 L380,200 L420,200 L420,130 L450,130 L450,200 L500,200 L500,80 L560,80 L560,200 L600,200 L600,100 L640,100 L640,200 L700,200 L700,50 L760,50 L760,200 L800,200 Z' fill='rgba(15, 23, 42, 0.2)'/%3E%3C/svg%3E");
        background-size: 200% 200%, 400px 120px;
        background-repeat: repeat-x, repeat-x;
        background-position: 0% 0%, bottom;
        animation: skyBlueShift 25s ease infinite, skylinePan 40s linear infinite;
        border-right: 1px solid rgba(255, 255, 255, 0.4);
    }
    
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div {
        color: #0F172A !important;
        font-weight: 600;
    }
    
    [data-testid="stSidebar"] .stRadio label p {
        color: #0F172A !important;
        font-weight: 700;
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.8);
        padding: 18px;
        border-radius: 14px;
        box-shadow: 0 10px 30px 0 rgba(2, 132, 199, 0.2);
    }
    div[data-testid="stMetric"] label {
        color: #1E293B !important;
        font-weight: 700;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #0369A1 !important;
        font-weight: 800;
    }

    .stButton button {
        background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(2, 132, 199, 0.4);
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #0369A1 0%, #075985 100%);
        box-shadow: 0 6px 20px rgba(2, 132, 199, 0.6);
        transform: translateY(-1px);
    }

    h1, h2, h3 {
        color: #0F172A;
        font-weight: 800;
        letter-spacing: -0.025em;
        text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    hr {
        border-color: rgba(255, 255, 255, 0.6);
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE UTILITIES ---
def run_query(query, params=(), fetch=True):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query, params)
    if fetch:
        result = cursor.fetchall()
        conn.close()
        return result
    conn.commit()
    conn.close()

def log_event_ui(user_id, event_name):
    now = datetime.now().isoformat()
    cohort_week = datetime.now().strftime("%Y-W%V")
    run_query(
        "INSERT INTO telemetry_events (user_id, event_name, timestamp, cohort_week) VALUES (?, ?, ?, ?)",
        (user_id, event_name, now, cohort_week),
        fetch=False
    )

# --- SESSION STATE & AUTH MANAGEMENT ---
if "logged_in_user_id" not in st.session_state:
    st.session_state.logged_in_user_id = None

# Fetch all existing users from DB for fallback or reference
all_db_users = run_query("SELECT user_id, username, entity_type, onboarding_complete, phone_number, role FROM users")

# ==========================================
# AUTH / PHONE NUMBER & PASSWORD GATEWAY
# ==========================================
if st.session_state.logged_in_user_id is None:
    st.title("💸 NewMoneySync — Secure Access Gateway")
    st.markdown("Authenticate securely using your phone number or access profile.")

    auth_tab1, auth_tab2, auth_tab3 = st.tabs(["📱 Standard Sign In (Phone Only)", "🔐 Developer / Secure Password Sign In", "✨ Register Business Profile"])

    with auth_tab1:
        st.subheader("Standard User Sign In")
        st.markdown("Enter your registered phone number for quick access.")
        with st.form("quick_login_form"):
            quick_phone_input = st.text_input("Phone Number", placeholder="e.g. +2348000000000", key="quick_phone")
            submitted_quick = st.form_submit_button("Access Platform", type="primary")

            if submitted_quick:
                if quick_phone_input.strip():
                    user_match = run_query(
                        "SELECT user_id, username FROM users WHERE phone_number = ?", 
                        (quick_phone_input.strip(),)
                    )
                    
                    if user_match:
                        db_user_id, db_username = user_match[0]
                        st.session_state.logged_in_user_id = db_user_id
                        st.success(f"Welcome back, {db_username}!")
                        st.rerun()
                    else:
                        st.error("Phone number not found. Please register an account.")
                else:
                    st.warning("Please enter your phone number.")

    with auth_tab2:
        st.subheader("Developer / Secure Password Sign In")
        with st.form("login_form"):
            phone_input = st.text_input("Phone Number", placeholder="e.g. +2348000000000")
            password_input = st.text_input("Password", type="password", placeholder="Enter your secure password")
            submitted_login = st.form_submit_button("Access Developer Portal", type="primary")

            if submitted_login:
                if phone_input.strip() and password_input.strip():
                    user_match = run_query(
                        "SELECT user_id, username, password_hash, role FROM users WHERE phone_number = ?", 
                        (phone_input.strip(),)
                    )
                    
                    if user_match:
                        db_user_id, db_username, db_pass, db_role = user_match[0]
                        
                        # Enforce password check and developer role validation
                        if db_role == 'developer':
                            if db_pass == password_input or (not db_pass and password_input == "password"):
                                st.session_state.logged_in_user_id = db_user_id
                                st.success(f"Welcome back, Developer {db_username}!")
                                st.rerun()
                            else:
                                st.error("Incorrect developer password.")
                        else:
                            st.error("This portal requires a developer role. Please use Standard Sign In.")
                    else:
                        st.error("Phone number not found.")
                else:
                    st.warning("Please enter both phone number and password.")

    with auth_tab3:
        st.subheader("Register New Account")
        with st.form("new_user_reg_form"):
            new_username = st.text_input("Business / Profile Name", placeholder="e.g. Apex Global Solutions")
            new_phone = st.text_input("Phone Number", placeholder="e.g. +2348000000000")
            new_password = st.text_input("Create Password", type="password", placeholder="Choose a secure password")
            new_email = st.text_input("Work Email", placeholder="founder@company.com")
            new_entity = st.selectbox("Entity Type", ["Freelancer", "Small Business (< ₦100M Turnover)", "Registered Corporation", "Cooperative Society"])
            new_turnover = st.number_input("Estimated Annual Turnover ($)", min_value=0.0, value=25000.0)
            
            submitted_reg = st.form_submit_button("Create Account & Start Onboarding")
            if submitted_reg:
                if new_username.strip() and new_phone.strip() and new_password.strip():
                    # Check if phone already exists
                    existing_phone = run_query("SELECT user_id FROM users WHERE phone_number = ?", (new_phone.strip(),))
                    if existing_phone:
                        st.error("An account with this phone number already exists. Please log in.")
                    else:
                        signup_date = datetime.now().isoformat()
                        cohort_week = datetime.now().strftime("%Y-W%V")
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute(
                            """INSERT INTO users (username, email, phone_number, password_hash, role, tier, entity_type, annual_turnover, tax_bracket_rate, coop_split_rate, traffic_source, signup_date, cohort_week, primary_intent, onboarding_complete) 
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (new_username, new_email, new_phone.strip(), new_password, "standard", "paid", new_entity, new_turnover, 7.5, 5.0, "direct_signup", signup_date, cohort_week, "Global Inflows & Settlements", 0)
                        )
                        new_id = cursor.lastrowid
                        conn.commit()
                        conn.close()
                        
                        st.session_state.logged_in_user_id = new_id
                        st.success(f"Account created for {new_username}! Initializing...")
                        st.rerun()
                else:
                    st.warning("Please provide a business name, phone number, and password.")

else:
    # Fetch active user details including their role
    active_user_row = run_query(
        "SELECT user_id, username, entity_type, annual_turnover, coop_split_rate, onboarding_complete, phone_number, role FROM users WHERE user_id = ?", 
        (st.session_state.logged_in_user_id,)
    )
    
    if not active_user_row:
        # Fallback if user ID was deleted
        st.session_state.logged_in_user_id = None
        st.rerun()

    active_user = active_user_row[0]
    active_user_id = active_user[0]
    active_username = active_user[1]
    onboarding_status = active_user[5] if active_user[5] is not None else 0
    active_phone = active_user[6] or "N/A"
    active_role = active_user[7] if len(active_user) > 7 and active_user[7] else "standard"

    # ==========================================
    # ONBOARDING WIZARD SCREEN (IF NOT COMPLETE)
    # ==========================================
    if onboarding_status == 0:
        st.title(f"🚀 Welcome to NewMoneySync, {active_username}")
        st.markdown("Let’s configure your financial operating system to match your exact business model before unlocking the dashboard.")

        with st.form("onboarding_wizard_form"):
            st.subheader("Step 1: What is your primary objective today?")
            primary_intent = st.selectbox(
                "Select your main use case",
                [
                    "Global Inflows & Multi-Asset Settlements (Invoicing & Crypto/Fiat Rails)",
                    "Team Payroll & Contractor Dispersals (Global & Local Pay-runs)",
                    "Cooperative & Esusu Thrift Management (Group Collections & Bulk Uploads)",
                    "Regulatory Grants & CBN Intervention Funding (Matchmaking & Dossiers)"
                ]
            )

            st.subheader("Step 2: Entity & Compliance Classification")
            business_name = st.text_input("Business / Organization Name", value=active_username)
            entity_class = st.selectbox("Entity Type", ["Freelancer", "Small Business (< ₦100M Turnover)", "Registered Corporation", "Cooperative Society"], index=["Freelancer", "Small Business (< ₦100M Turnover)", "Registered Corporation", "Cooperative Society"].index(active_user[2]) if active_user[2] in ["Freelancer", "Small Business (< ₦100M Turnover)", "Registered Corporation", "Cooperative Society"] else 0)
            annual_rev = st.number_input("Estimated Annual Turnover ($)", min_value=0.0, value=active_user[3] if active_user[3] else 15000.0)
            preferred_rail = st.selectbox("Primary Settlement Asset", ["USDC / USDT Stablecoins", "NGN Local Fiat", "USD Bank Wire / ACH", "Multi-Rail Hybrid"])

            submitted_wizard = st.form_submit_button("Complete Setup & Launch Dashboard", type="primary")
            if submitted_wizard:
                calculated_tax = 0.0 if "Small Business" in entity_class and annual_rev <= 65000 else 7.5
                run_query(
                    "UPDATE users SET username = ?, entity_type = ?, annual_turnover = ?, tax_bracket_rate = ?, primary_intent = ?, onboarding_complete = 1 WHERE user_id = ?",
                    (business_name, entity_class, annual_rev, calculated_tax, primary_intent, active_user_id),
                    fetch=False
                )
                log_event_ui(active_user_id, f"onboarding_completed_{primary_intent[:10]}")
                st.success("Setup complete! Initializing your custom workspace...")
                st.rerun()

    else:
        # --- GLOBAL VIEW CONTEXT & USER DEFAULTS ---
        user_record = run_query(
            "SELECT username, entity_type, annual_turnover FROM users WHERE user_id = ?", 
            (active_user_id,)
        )

        if user_record and user_record[0]:
            u_name, entity_type, annual_turnover = user_record[0]
        else:
            u_name, entity_type, annual_turnover = "Joseph", "SME / Tech & Creative", 5000000.0

        # Define programs list for CBN Intervention Matchmaker
        programs = [
            {
                "name": "BOI MSME Intervention Fund",
                "type": "Low-Interest Loan (9% P.A.)",
                "max_amount": "₦10,000,000 (~$12,000)",
                "interest": "9% per annum",
                "min_turnover": 1000000.0,
                "sector": "Technology & Manufacturing",
                "eligibility_check": lambda e, rev: rev >= 1000000.0,
                "description": "Targeted support for technology and manufacturing enterprises."
            },
            {
                "name": "CBN Creative Industry Financing Initiative",
                "type": "Concessionary Loan & Grant",
                "max_amount": "₦5,000,000 (~$6,000)",
                "interest": "2% - 9% per annum",
                "min_turnover": 500000.0,
                "sector": "Creative, Media & Entertainment",
                "eligibility_check": lambda e, rev: rev >= 500000.0,
                "description": "Financing for software, music production, media, and creative ventures."
            },
            {
                "name": "SMEDAN Matching Fund",
                "type": "Federal Grant & Equipment Support",
                "max_amount": "₦2,000,000 Direct Grant",
                "interest": "0% (Non-repayable grant)",
                "min_turnover": 200000.0,
                "sector": "General Commerce & Retail",
                "eligibility_check": lambda e, rev: rev >= 200000.0,
                "description": "Designed to scale micro-enterprises and growing digital/industrial startups."
            }
        ]

        # --- SIDEBAR NAVIGATION & LOGOUT ---
        st.sidebar.title("NewMoneySync 💸")
        st.sidebar.caption(f"Mode: {active_role.upper()}")

        menu_options = [
            "Dashboard & Telemetry", 
            "Invoicing & Stablecoin Settlement", 
            "Webhook Simulation (Auto-Pay)",
            "Payroll & Dispersals",
            "User Settings & Automation Rules",
            "Cooperative Ledger (GRP-01)",
            "Tax & Compliance Engine",
            "CBN Intervention Matchmaker (GOV-01)",
            "OmniSync Retail Intelligence"
        ]

        if active_role == 'developer':
            menu_options.insert(0, "🛠️ Developer Control Center")

        menu = st.sidebar.radio("Navigation", menu_options)

        st.sidebar.markdown("---")
        st.sidebar.markdown(f"👤 **Logged in as:**\n`{active_username}`\n📱 `{active_phone}`")
        
        if st.sidebar.button("🚪 Logout / Switch Profile"):
            st.session_state.logged_in_user_id = None
            st.rerun()

        # ==========================================
        # 0. DEVELOPER CONTROL CENTER (IF DEVELOPER)
        # ==========================================
        if menu == "🛠️ Developer Control Center":
            st.title("🛠️ Developer Control Center")
            st.markdown("System-wide administrative oversight, global telemetry, and active session management.")

            col_dc1, col_dc2, col_dc3 = st.columns(3)
            with col_dc1:
                st.metric("System Environment", "Mainnet / Production")
            with col_dc2:
                st.metric("Database Active File", DB_NAME)
            with col_dc3:
                st.metric("Active Role Access", active_role.upper())

            st.markdown("---")
            st.subheader("Global User Directory & Role Management")
            
            all_users_df = pd.read_sql("SELECT user_id, username, phone_number, role, entity_type, annual_turnover, onboarding_complete FROM users", sqlite3.connect(DB_NAME))
            st.dataframe(all_users_df, use_container_width=True)

            st.markdown("---")
            st.subheader("Live User Retail & Inventory Activity")
            try:
                live_products_df = pd.read_sql("""
                    SELECT p.product_id, p.user_id, u.username, u.phone_number, p.name, p.category, p.cost_price, p.selling_price, i.quantity_on_hand, p.created_at
                    FROM omnisync_products p
                    LEFT JOIN users u ON p.user_id = u.user_id
                    LEFT JOIN omnisync_inventory i ON p.product_id = i.product_id
                """, sqlite3.connect(DB_NAME))
                if not live_products_df.empty:
                    st.dataframe(live_products_df, use_container_width=True)
                else:
                    st.info("No retail products logged by users yet.")
            except Exception as e:
                st.info("Awaiting first user retail inputs...")

            st.markdown("### Quick Developer Actions")
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("🔄 Reset Active Session State"):
                    st.session_state.clear()
                    st.success("Session state cache cleared successfully!")
                    st.rerun()
            with col_act2:
                if st.button("📊 Force Refresh Telemetry Cache"):
                    st.success("Telemetry cache reloaded.")

        # ==========================================
        # 1. DASHBOARD & TELEMETRY VIEW
        # ==========================================
        elif menu == "Dashboard & Telemetry":
            st.title("📊 NewMoneySync Telemetry & Metrics Dashboard")
            st.markdown("Real-time automated tracking across your core MVP metrics.")

            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                st.markdown("🟢 **USDC Gateway:** `Active ($1.00 Peg)`")
            with col_t2:
                st.markdown("🔵 **USDT Settlement:** `Operational`")
            with col_t3:
                st.markdown("🪙 **VASP Rail:** `Mainnet Connected`")

            st.markdown("---")

            df_users = pd.read_sql("SELECT user_id, username, email, phone_number, entity_type, tier, cohort_week FROM users", sqlite3.connect(DB_NAME))
            df_events = pd.read_sql("SELECT * FROM telemetry_events WHERE user_id = ?", sqlite3.connect(DB_NAME), params=(active_user_id,))
            df_invoices = pd.read_sql("SELECT * FROM invoices WHERE user_id = ?", sqlite3.connect(DB_NAME), params=(active_user_id,))

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Registered Users", len(df_users))
            with col2:
                paid_count = len(df_users[df_users['tier'] == 'paid']) if not df_users.empty else 0
                st.metric("Paid Conversion Count", paid_count)
            with col3:
                st.metric("Total Logged Actions", len(df_events))
            with col4:
                settled_inv = len(df_invoices[df_invoices['status'] == 'settled']) if not df_invoices.empty else 0
                st.metric("Settled Invoices", settled_inv)

            st.markdown("---")
            
            tab1, tab2, tab3 = st.tabs(["Traffic & Cohorts", "Measurable Actions Log", "Retention & Conversion Data"])
            with tab1:
                if not df_users.empty:
                    st.dataframe(df_users[['user_id', 'username', 'phone_number', 'cohort_week', 'tier']], use_container_width=True)
                else:
                    st.info("No user data available.")
            with tab2:
                if not df_events.empty:
                    st.dataframe(df_events, use_container_width=True)
                else:
                    st.info("No telemetry events logged yet.")
            with tab3:
                if not df_invoices.empty:
                    st.dataframe(df_invoices, use_container_width=True)
                else:
                    st.info("No invoice records available.")

        # ==========================================
        # 2. INVOICING & MULTI-ASSET SETTLEMENT
        # ==========================================
        elif menu == "Invoicing & Stablecoin Settlement":
            st.title("⚡ Multi-Asset Invoicing & Settlement Engine")
            st.markdown("Create digital invoices bridging **Real Cash (Fiat)**, **Stablecoins (USDC/USDT)**, and **Decentralized Cryptocurrencies**.")

            col_rail1, col_rail2, col_rail3 = st.columns(3)
            with col_rail1:
                st.markdown("💵 **Fiat Cash Rail:** `Active (ACH/NIBSS)`")
            with col_rail2:
                st.markdown("🟢 **Stablecoin Rail:** `Active (USDC/USDT Peg)`")
            with col_rail3:
                st.markdown("🪙 **Crypto Layer:** `Active (BTC/ETH Swap)`")

            st.markdown("---")

            with st.form("invoice_form"):
                client_name = st.text_input("Client Name / Organization")
                amount = st.number_input("Invoice Amount ($)", min_value=1.0, value=1500.0)
                
                asset_category = st.selectbox(
                    "Select Payment & Settlement Rail", 
                    [
                        "Stablecoin (USDC - Base / Polygon)", 
                        "Stablecoin (USDT - Tron / Ethereum)", 
                        "Real Cash / Fiat (USD Bank Wire / ACH)", 
                        "Real Cash / Fiat (NGN Local Bank Transfer)",
                        "Cryptocurrency (Bitcoin - BTC)", 
                        "Cryptocurrency (Ethereum - ETH)"
                    ]
                )
                
                submitted = st.form_submit_button("Generate Multi-Asset Smart Invoice")
                if submitted and client_name:
                    created_at = datetime.now().isoformat()
                    run_query(
                        "INSERT INTO invoices (user_id, client_name, amount, asset_type, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (active_user_id, client_name, amount, asset_category, "pending", created_at),
                        fetch=False
                    )
                    log_event_ui(active_user_id, "multi_asset_invoice_created")
                    st.success(f"Smart Invoice for ${amount:,.2f} routed via **{asset_category}** generated successfully for {client_name}!")
                elif submitted:
                    st.warning("Please enter a client name.")

            st.markdown("---")
            st.subheader("All Invoices Across Fiat, Stablecoins & Crypto")
            invoices = run_query("SELECT invoice_id, client_name, amount, asset_type, status, payment_tx_hash, created_at FROM invoices WHERE user_id = ?", (active_user_id,))
            if invoices:
                df_inv = pd.DataFrame(invoices, columns=["ID", "Client", "Amount ($)", "Rail / Asset Type", "Status", "Tx Reference", "Created At"])
                st.dataframe(df_inv, use_container_width=True)
            else:
                st.info("No invoices created yet.")

        # ==========================================
        # 3. WEBHOOK SIMULATION (AUTO-PAY)
        # ==========================================
        elif menu == "Webhook Simulation (Auto-Pay)":
            st.title("🔌 VASP / Blockchain Webhook Simulation")
            st.markdown("Simulate an incoming mainnet stablecoin transfer.")

            pending_invoices = run_query("SELECT invoice_id, client_name, amount, asset_type FROM invoices WHERE user_id = ? AND status = 'pending'", (active_user_id,))
            if pending_invoices:
                selected_inv = st.selectbox("Select Pending Invoice", pending_invoices, format_func=lambda x: f"Invoice #{x[0]} - {x[1]} (${x[2]} {x[3]})")
                if st.button("Simulate Incoming Mainnet Webhook (Pay Now)"):
                    inv_id, client, amt, asset = selected_inv
                    simulated_hash = f"0x9f8c...{inv_id}abc712_base"
                    run_query("UPDATE invoices SET status = 'settled', payment_tx_hash = ? WHERE invoice_id = ?", (simulated_hash, inv_id), fetch=False)
                    log_event_ui(active_user_id, "invoice_settled_via_webhook")
                    
                    user_data = run_query("SELECT coop_split_rate, tax_bracket_rate FROM users WHERE user_id = ?", (active_user_id,))[0]
                    tax_res = amt * (user_data[1] / 100.0)
                    coop_res = amt * (user_data[0] / 100.0)
                    net = amt - (tax_res + coop_res)
                    
                    st.success(f"⚡ Webhook received! Tx Hash: `{simulated_hash}`")
                    st.markdown(f"**Net Payout:** ${net:.2f} | **Tax Reserved:** ${tax_res:.2f} | **Coop Split:** ${coop_res:.2f}")
                    st.rerun()
            else:
                st.info("No pending invoices found.")

        # ==========================================
        # 4. PAYROLL & DISPERSALS MODULE
        # ==========================================
        elif menu == "Payroll & Dispersals":
            st.title("🏢 Multi-Asset Payroll & Dispersals Engine")
            st.markdown("Manage global team compensation across fiat and stablecoin rails with automated ledger posting.")

            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("Team Directory")
                employees = run_query("SELECT employee_id, full_name, role, payout_rail, salary_amount FROM payroll_directory WHERE user_id = ?", (active_user_id,))
                if employees:
                    df_emp = pd.DataFrame(employees, columns=["ID", "Full Name", "Role", "Rail", "Monthly Salary ($)"])
                    st.dataframe(df_emp, use_container_width=True)
                else:
                    st.info("No employees or contractors added to the payroll directory yet.")

                with st.form("add_employee_form"):
                    st.markdown("**Add New Recipient**")
                    emp_name = st.text_input("Full Name")
                    emp_role = st.text_input("Role / Title")
                    emp_rail = st.selectbox("Preferred Payout Rail", ["USDC", "USDT", "NGN Fiat", "USD Fiat"])
                    emp_salary = st.number_input("Monthly Compensation Amount", min_value=0.0, step=100.0)
                    
                    submitted = st.form_submit_button("Add to Directory")
                    if submitted and emp_name:
                        joined = datetime.now().isoformat()
                        run_query(
                            "INSERT INTO payroll_directory (user_id, full_name, role, payout_rail, salary_amount, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                            (active_user_id, emp_name, emp_role, emp_rail, emp_salary, joined),
                            fetch=False
                        )
                        log_event_ui(active_user_id, "payroll_employee_added")
                        st.success(f"Added {emp_name} successfully!")
                        st.rerun()
                    elif submitted:
                        st.warning("Please enter a recipient name.")

            with col2:
                st.subheader("Execute Payroll Run")
                st.markdown("Disburse active monthly salaries across selected rails.")
                
                all_emp = run_query("SELECT payout_rail, salary_amount FROM payroll_directory WHERE user_id = ?", (active_user_id,))
                total_payroll_usd = sum([e[1] for e in all_emp if "USD" in e[0] or e[0] in ["USDC", "USDT"]])
                total_payroll_ngn = sum([e[1] for e in all_emp if "NGN" in e[0]])
                
                st.metric(label="Pending Stablecoin/USD Run", value=f"${total_payroll_usd:,.2f}")
                st.metric(label="Pending NGN Fiat Run", value=f"₦{total_payroll_ngn:,.2f}")

                if st.button("🚀 Execute Monthly Payroll Run", type="primary"):
                    if all_emp:
                        run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                        total_combined = total_payroll_usd + (total_payroll_ngn / 1500.0)
                        
                        run_query(
                            "INSERT INTO payroll_history (user_id, run_date, recipient_count, total_amount, currency_summary, status) VALUES (?, ?, ?, ?, ?, ?)",
                            (active_user_id, run_date, len(all_emp), total_combined, f"USD: ${total_payroll_usd:,.2f} | NGN: ₦{total_payroll_ngn:,.2f}", "Settled"),
                            fetch=False
                        )
                        log_event_ui(active_user_id, "payroll_run_executed")
                        st.success("Payroll executed successfully! Double-entry ledger updated automatically.")
                        st.balloons()
                        st.rerun()
                    else:
                        st.warning("No active employees found to run payroll for.")

            st.divider()
            st.subheader("Payroll Dispersal & Ledger Logs")
            history = run_query("SELECT run_date, recipient_count, total_amount, currency_summary, status FROM payroll_history WHERE user_id = ?", (active_user_id,))
            if history:
                df_hist = pd.DataFrame(history, columns=["Run Date", "Recipients", "Total Amount (USD Equiv)", "Currency Summary", "Status"])
                st.dataframe(df_hist, use_container_width=True)
            else:
                st.info("No payroll runs executed yet this cycle.")

        # ==========================================
        # 5. USER SETTINGS & AUTOMATION RULES
        # ==========================================
        elif menu == "User Settings & Automation Rules":
            st.title("⚙️ User Settings & Custom Automation Rules")
            user_info = run_query("SELECT entity_type, annual_turnover, tax_bracket_rate, coop_split_rate, phone_number FROM users WHERE user_id = ?", (active_user_id,))[0]
            
            with st.form("settings_form"):
                phone_num = st.text_input("Phone Number", value=user_info[4] if user_info[4] else "")
                new_pass = st.text_input("New Password (leave blank to keep current)", type="password")
                entity_type = st.selectbox("Entity Classification", ["Freelancer", "Small Business (< ₦100M Turnover)", "Registered Corporation"], index=["Freelancer", "Small Business (< ₦100M Turnover)", "Registered Corporation"].index(user_info[0]) if user_info[0] in ["Freelancer", "Small Business (< ₦100M Turnover)", "Registered Corporation"] else 0)
                annual_turnover = st.number_input("Estimated Annual Revenue ($)", min_value=0.0, value=user_info[1] if user_info[1] else 15000.0)
                coop_split_rate = st.slider("Cooperative Pool Allocation (%)", min_value=0.0, max_value=25.0, value=user_info[3] if user_info[3] else 5.0, step=0.5)
                
                if st.form_submit_button("Save Automation Rules"):
                    calculated_tax = 0.0 if entity_type == "Small Business (< ₦100M Turnover)" and annual_turnover <= 65000 else 7.5
                    if new_pass.strip():
                        run_query("UPDATE users SET phone_number = ?, password_hash = ?, entity_type = ?, annual_turnover = ?, tax_bracket_rate = ?, coop_split_rate = ? WHERE user_id = ?", 
                                  (phone_num, new_pass, entity_type, annual_turnover, calculated_tax, coop_split_rate, active_user_id), fetch=False)
                    else:
                        run_query("UPDATE users SET phone_number = ?, entity_type = ?, annual_turnover = ?, tax_bracket_rate = ?, coop_split_rate = ? WHERE user_id = ?", 
                                  (phone_num, entity_type, annual_turnover, calculated_tax, coop_split_rate, active_user_id), fetch=False)
                    st.success("Automation rules updated successfully!")
                    st.rerun()

        # ==========================================
        # 6. COOPERATIVE LEDGER (GRP-01)
        # ==========================================
        elif menu == "Cooperative Ledger (GRP-01)":
            st.title("👥 Corporate Cooperative & Esusu Thrift Ledger")
            st.markdown("Manage employee thrift collections, micro-loans, and **bulk member uploads via CSV**.")
            
            col_a, col_b = st.columns([1, 1])
            
            with col_a:
                st.subheader("Option A: Add Single Member")
                with st.form("single_member_form"):
                    member_name = st.text_input("Member Full Name")
                    member_email = st.text_input("Email Address")
                    department = st.text_input("Department / Unit")
                    monthly_contrib = st.number_input("Monthly Contribution ($)", min_value=0.0, value=50.0)
                    
                    if st.form_submit_button("Add Member"):
                        if member_name:
                            joined = datetime.now().isoformat()
                            run_query(
                                "INSERT INTO cooperative_members (user_id, member_name, email, department, monthly_contrib, joined_at) VALUES (?, ?, ?, ?, ?, ?)",
                                (active_user_id, member_name, member_email, department, monthly_contrib, joined),
                                fetch=False
                            )
                            log_event_ui(active_user_id, "cooperative_member_added")
                            st.success(f"Added {member_name} successfully!")
                            st.rerun()
                        else:
                            st.warning("Please enter a member name.")

            with col_b:
                st.subheader("Option B: Bulk CSV Upload")
                st.markdown("Upload a CSV file containing columns: `member_name`, `email`, `department`, `monthly_contrib`")
                
                sample_csv = "member_name,email,department,monthly_contrib\nJane Doe,jane@company.com,Engineering,100.0\nJohn Smith,john@company.com,Product,75.0"
                st.download_button("Download CSV Template", data=sample_csv, file_name="coop_members_template.csv", mime="text/csv")
                
                uploaded_file = st.file_uploader("Upload Member CSV", type=["csv"])
                if uploaded_file is not None:
                    try:
                        df_upload = pd.read_csv(uploaded_file)
                        required_cols = {"member_name", "email", "department", "monthly_contrib"}
                        if required_cols.issubset(df_upload.columns):
                            if st.button("Process Bulk Import"):
                                joined = datetime.now().isoformat()
                                conn = sqlite3.connect(DB_NAME)
                                cursor = conn.cursor()
                                count = 0
                                for _, row in df_upload.iterrows():
                                    cursor.execute(
                                        "INSERT INTO cooperative_members (user_id, member_name, email, department, monthly_contrib, joined_at) VALUES (?, ?, ?, ?, ?, ?)",
                                        (active_user_id, row['member_name'], row['email'], row['department'], row['monthly_contrib'], joined)
                                    )
                                    count += 1
                                conn.commit()
                                conn.close()
                                log_event_ui(active_user_id, "cooperative_bulk_csv_imported")
                                st.success(f"Successfully imported {count} cooperative members from CSV!")
                                st.rerun()
                        else:
                            st.error(f"CSV format invalid. Must contain columns: {required_cols}")
                    except Exception as e:
                        st.error(f"Error parsing CSV file: {e}")

            st.markdown("---")
            st.subheader("Active Cooperative Members Directory")
            members = run_query("SELECT member_id, member_name, email, department, monthly_contrib, joined_at FROM cooperative_members WHERE user_id = ?", (active_user_id,))
            if members:
                df_members = pd.DataFrame(members, columns=["ID", "Name", "Email", "Department", "Monthly Contribution ($)", "Joined At"])
                st.dataframe(df_members, use_container_width=True)
                
                total_monthly_pool = df_members["Monthly Contribution ($)"].sum()
                st.metric("Total Monthly Esusu / Thrift Pool Collection", f"${total_monthly_pool:,.2f}")
            else:
                st.info("No cooperative members registered yet. Add members individually or via CSV upload above!")

        # ==========================================
        # 7. TAX & COMPLIANCE ENGINE
        # ==========================================
        elif menu == "Tax & Compliance Engine":
            st.title("📋 Tax & Compliance Engine (TAX-01)")
            user_data = run_query("SELECT tax_bracket_rate, entity_type FROM users WHERE user_id = ?", (active_user_id,))[0]
            tax_rate = user_data[0]
            settled_invoices = run_query("SELECT amount FROM invoices WHERE user_id = ? AND status = 'settled'", (active_user_id,))
            
            if settled_invoices:
                total_settled = sum([inv[0] for inv in settled_invoices])
                total_tax = total_settled * (tax_rate / 100.0)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Settled Revenue", f"${total_settled:.2f}")
                with col2:
                    st.metric("Active Tax Rate Profile", f"{tax_rate}%")
                with col3:
                    st.metric("Total Reserved Tax", f"${total_tax:.2f}")
            else:
                st.info("No settled revenue found.")

        # ==========================================
        # 8. CBN INTERVENTION MATCHMAKER (GOV-01)
        # ==========================================
        elif menu == "CBN Intervention Matchmaker (GOV-01)":
            st.title("🇳🇬 Government & CBN Intervention Matchmaker (GOV-01)")
            st.markdown("Algorithmic matching engine linking your business profile with active Nigerian federal grants, single-digit loans, and SME intervention funds.")

            st.info(f"Analyzing profile for **{u_name}** | Entity: **{entity_type}** | Est. Annual Revenue: **${annual_turnover:,.2f}**")

            st.markdown("### 🔍 Live Program Eligibility Assessment")
            
            for prog in programs:
                is_eligible = prog["eligibility_check"](entity_type, annual_turnover)
                
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"#### {prog['name']}")
                        st.caption(prog['description'])
                        st.markdown(f"**Type:** {prog['type']} | **Max Cap:** {prog['max_amount']} | **Interest:** {prog['interest']}")
                    
                    with col2:
                        if is_eligible:
                            st.success("✅ Eligible Match")
                            button_key = f"btn_{prog['name'].replace(' ', '_').replace('/', '_')}"
                            if st.button("Generate Dossier", key=button_key):
                                log_event_ui(active_user_id, f"matched_intervention_{prog['name'][:10]}")
                                st.session_state[f"dossier_{button_key}"] = True
                        else:
                            st.warning("⚠️ Review Criteria")
                    
                    target_key = f"btn_{prog['name'].replace(' ', '_').replace('/', '_')}"
                    if st.session_state.get(f"dossier_{target_key}", False):
                        specific_dossier = f"""OFFICIAL APPLICATION DOSSIER: {prog['name'].upper()}
=====================================================
APPLICANT PROFILE:
- Business Name: {u_name}
- Legal Classification: {entity_type}
- Declared Annual Revenue: ${annual_turnover:,.2f}
- Compliance Status: Verified via NewMoneySync Ledger

FUND SPECIFICATIONS:
- Fund Type: {prog['type']}
- Maximum Allocation: {prog['max_amount']}
- Stated Interest: {prog['interest']}
- Objective: {prog['description']}

DECLARATION:
The applicant has met the automated eligibility benchmark criteria set forth by NewMoneySync Gov-01 Engine. All digital telemetry and invoice transaction records are securely logged for audit verification.
=====================================================
"""
                        st.download_button(
                            label=f"📥 Download Ready Dossier for {prog['name']}",
                            data=specific_dossier,
                            file_name=f"Dossier_{prog['name'].replace(' ', '_').replace('/', '_')}.txt",
                            mime="text/plain",
                            key=f"download_{target_key}"
                        )
                    
                    st.markdown("---")
            
        # ==========================================
        # 9. OMNISYNC RETAIL INTELLIGENCE MODULE
        # ==========================================
        elif menu == "OmniSync Retail Intelligence":
            st.title("📦 OmniSync Retail Intelligence")
            st.markdown("Bridge physical retail storefronts into your financial ledger using Gemini multimodal AI.")

            from omnisync.services import parse_retail_input_with_gemini

            omni_tab1, omni_tab2, omni_tab3 = st.tabs(["📥 Multimodal Intake", "📊 Storefront & Valuation", "⚡ Sales & Restock Tracker"])

            with omni_tab1:
                st.subheader("Instant Shelf Onboarding")
                intake_mode = st.radio("Choose Intake Method", ["Voice Note (with text preview)", "Text Description", "Upload Shelf Photo"])

                # Handle extraction results review session state initialization
                if 'pending_inventory' not in st.session_state:
                    st.session_state['pending_inventory'] = []

                if intake_mode == "Upload Shelf Photo":
                    photo_tab1, photo_tab2 = st.tabs(["📷 Take Live Photo", "📁 Camera Roll Gallery"])
                    
                    image_bytes = None
                    
                    with photo_tab1:
                        camera_image = st.camera_input("Take a photo of the shelf inventory", key="shelf_camera_input")
                        if camera_image is not None:
                            image_bytes = camera_image.getvalue()
                            
                    with photo_tab2:
                        uploaded_shelf = st.file_uploader("Choose an existing photo from your device", type=["jpg", "png", "jpeg"], key="shelf_file_uploader")
                        if uploaded_shelf is not None:
                            image_bytes = uploaded_shelf.getvalue()
                            st.image(uploaded_shelf, caption="Target Shelf View", use_container_width=True)

                    if image_bytes is not None:
                        if st.button("Process Shelf with Gemini AI"):
                            with st.spinner("Analyzing physical stock via Gemini..."):
                                try:
                                    parsed_items = parse_retail_input_with_gemini(image_bytes=image_bytes)
                                    if isinstance(parsed_items, list):
                                        for item in parsed_items:
                                            if item.get('cost_price') is None:
                                                item['cost_price'] = 0.0
                                            if item.get('selling_price') is None:
                                                item['selling_price'] = 0.0
                                            if item.get('quantity') is None:
                                                item['quantity'] = 1
                                        st.session_state['pending_inventory'] = parsed_items
                                        st.success("Successfully extracted inventory catalog! Please review and update prices below.")
                                        log_event_ui(active_user_id, "omnisync_shelf_photo_imported")
                                except Exception as e:
                                    st.error(f"Error parsing image: {e}")
                    else:
                        st.info("Snap a live photo or select an existing picture from your camera roll above to begin.")                    

                elif intake_mode == "Voice Note (with text preview)":
                    st.markdown("🎙️ **Record your stock note:**")
                    audio_file = st.audio_input("Record inventory voice note")
                    
                    # Initialize session state variables
                    if 'editable_inventory_text' not in st.session_state:
                        st.session_state['editable_inventory_text'] = ""
                    if 'last_audio_file_id' not in st.session_state:
                        st.session_state['last_audio_file_id'] = None
                        
                    # Automatically transcribe when a new audio recording is detected
                    if audio_file is not None:
                        current_file_id = getattr(audio_file, 'file_id', id(audio_file))
                        if st.session_state['last_audio_file_id'] != current_file_id:
                            with st.spinner("Transcribing your voice via Gemini..."):
                                try:
                                    audio_bytes = audio_file.getvalue()
                                    mime_type = getattr(audio_file, 'type', 'audio/wav')
                                    transcribed_text = transcribe_audio_with_gemini(audio_bytes, mime_type=mime_type)
                                    st.session_state['editable_inventory_text'] = transcribed_text
                                    st.session_state['last_audio_file_id'] = current_file_id
                                    st.success("Transcription complete!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Could not transcribe automatically. Please try recording again or type your note. ({e})")
                    
                    inventory_text = st.text_area(
                        "Review and edit your transcribed inventory text here:",
                        key="editable_inventory_text"
                    )
                    
                    if st.button("Process Final Inventory Text"):
                        if inventory_text.strip():
                            with st.spinner("Structuring items and calculating margins..."):
                                try:
                                    parsed_items = parse_retail_input_with_gemini(raw_input_text=inventory_text)
                                    if isinstance(parsed_items, list):
                                        for item in parsed_items:
                                            if item.get('cost_price') is None:
                                                item['cost_price'] = 0.0
                                            if item.get('selling_price') is None:
                                                item['selling_price'] = 0.0
                                            if item.get('quantity') is None:
                                                item['quantity'] = 10
                                        st.session_state['pending_inventory'] = parsed_items
                                        st.success("Store catalog structured successfully! Please review and update prices below.")
                                        log_event_ui(active_user_id, "omnisync_voice_transcribed_imported")
                                except Exception as e:
                                    st.error(f"Error processing text: {e}")
                        else:
                            st.warning("The text box is empty. Record a voice note or type an item description first.")

                            
                else:
                    inventory_text = st.text_area(
                        "Type your inventory description", 
                        placeholder="e.g., '10 crates of Coca-Cola bought at 3000 NGN, selling at 4500 NGN.'"
                    )
                    
                    if st.button("Process Inventory with Gemini"):
                        if inventory_text.strip():
                            with st.spinner("Structuring items and calculating baseline margins via Gemini..."):
                                try:
                                    parsed_items = parse_retail_input_with_gemini(raw_input_text=inventory_text)
                                    if isinstance(parsed_items, list):
                                        for item in parsed_items:
                                            if item.get('cost_price') is None:
                                                item['cost_price'] = 0.0
                                            if item.get('selling_price') is None:
                                                item['selling_price'] = 0.0
                                            if item.get('quantity') is None:
                                                item['quantity'] = 10
                                        st.session_state['pending_inventory'] = parsed_items
                                        st.success("Store catalog structured successfully! Please review and update prices below.")
                                        log_event_ui(active_user_id, "omnisync_text_imported")
                                except Exception as e:
                                    st.error(f"Error processing text: {e}")
                        else:
                            st.warning("Please type an inventory description first.")

                # Interactive Review & Commit Pending Items Editor
                if st.session_state.get('pending_inventory'):
                    st.markdown("---")
                    st.subheader("📝 Review & Complete Pricing Details")
                    st.markdown("Review extracted items, add missing prices or quantities, then commit to your store database.")
                    
                    df_pending = pd.DataFrame(st.session_state['pending_inventory'])
                    edited_pending_df = st.data_editor(
                        df_pending,
                        num_rows="dynamic",
                        key="inventory_review_editor"
                    )
                    
                    if st.button("Commit Pending Items to Store Database", type="primary"):
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        for index, row in edited_pending_df.iterrows():
                            c_price = float(row['cost_price']) if row['cost_price'] is not None else 0.0
                            s_price = float(row['selling_price']) if row['selling_price'] is not None else 0.0
                            qty = int(row['quantity']) if row['quantity'] is not None else 1
                            cat = row.get('category', 'General')
                            
                            cursor.execute(
                                "INSERT INTO omnisync_products (user_id, name, category, cost_price, selling_price, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                (active_user_id, row['name'], cat, c_price, s_price, datetime.now().isoformat())
                            )
                            prod_id = cursor.lastrowid
                            cursor.execute(
                                "INSERT INTO omnisync_inventory (product_id, quantity_on_hand, updated_at) VALUES (?, ?, ?)",
                                (prod_id, qty, datetime.now().isoformat())
                            )
                        conn.commit()
                        conn.close()
                        st.session_state['pending_inventory'] = []
                        st.success("Inventory successfully saved to store database!")
                        st.balloons()
                        st.rerun()

            with omni_tab2:
                st.subheader("📊 Storefront Valuation & Live Price Management")
                st.markdown("Update cost prices, selling prices, categories, or stock quantities at any time.")
                
                query = """
                    SELECT p.product_id, p.name, p.category, p.cost_price, p.selling_price, i.quantity_on_hand, 
                           (i.quantity_on_hand * p.cost_price) as total_cost_valuation,
                           (i.quantity_on_hand * (p.selling_price - p.cost_price)) as potential_profit
                    FROM omnisync_products p
                    JOIN omnisync_inventory i ON p.product_id = i.product_id
                    WHERE p.user_id = ?
                """
                products_df = pd.read_sql(query, sqlite3.connect(DB_NAME), params=(active_user_id,))

                if not products_df.empty:
                    total_net_worth = products_df['total_cost_valuation'].sum()
                    total_potential_profit = products_df['potential_profit'].sum()

                    col_v1, col_v2 = st.columns(2)
                    with col_v1:
                        st.metric("Total Store Net Worth (Capital)", f"${total_net_worth:,.2f}")
                    with col_v2:
                        st.metric("Potential Gross Profit", f"${total_potential_profit:,.2f}")

                    st.markdown("---")
                    st.subheader("Interactive Catalog Management")
                    
                    updated_catalog = st.data_editor(
                        products_df,
                        column_config={
                            "product_id": "ID",
                            "name": "Product Name",
                            "category": "Category",
                            "cost_price": st.column_config.NumberColumn("Cost Price ($)", format="$%.2f", min_value=0.0),
                            "selling_price": st.column_config.NumberColumn("Selling Price ($)", format="$%.2f", min_value=0.0),
                            "quantity_on_hand": st.column_config.NumberColumn("Stock Qty", format="%d", min_value=0),
                            "total_cost_valuation": None,
                            "potential_profit": None
                        },
                        disabled=["product_id"],
                        hide_index=True,
                        key="catalog_editor"
                    )
                    
                    if st.button("Save Catalog & Price Updates", type="primary"):
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        for index, row in updated_catalog.iterrows():
                            cursor.execute(
                                "UPDATE omnisync_products SET name=?, category=?, cost_price=?, selling_price=? WHERE product_id=?",
                                (row['name'], row['category'], float(row['cost_price']), float(row['selling_price']), int(row['product_id']))
                            )
                            cursor.execute(
                                "UPDATE omnisync_inventory SET quantity_on_hand=?, updated_at=? WHERE product_id=?",
                                (int(row['quantity_on_hand']), datetime.now().isoformat(), int(row['product_id']))
                            )
                        conn.commit()
                        conn.close()
                        st.success("Store catalog and pricing updated successfully!")
                        st.rerun()
                else:
                    st.info("No retail products in your OmniSync catalog yet. Use the 'Multimodal Intake' tab to add items via photo or text.")

            with omni_tab3:
                st.subheader("Sales Velocity & Restock Alerts")
                st.markdown("Log physical shop sales to track fast-moving items and automate restocking schedules.")
                
                active_prods = run_query("SELECT p.product_id, p.name, i.quantity_on_hand FROM omnisync_products p JOIN omnisync_inventory i ON p.product_id = i.product_id WHERE p.user_id = ?", (active_user_id,))
                
                if active_prods:
                    with st.form("log_retail_sale_form"):
                        selected_product = st.selectbox("Select Sold Product", active_prods, format_func=lambda x: f"{x[1]} (Stock on hand: {x[2]})")
                        qty_sold = st.number_input("Quantity Sold", min_value=1, value=1)
                        
                        if st.form_submit_button("Record Sale & Update Inventory"):
                            prod_id = selected_product[0]
                            current_stock = selected_product[2]
                            
                            if qty_sold <= current_stock:
                                p_details = run_query("SELECT cost_price, selling_price FROM omnisync_products WHERE product_id = ?", (prod_id,))[0]
                                cp, sp = p_details[0], p_details[1]
                                rev = qty_sold * sp
                                cost = qty_sold * cp
                                profit = rev - cost
                                
                                conn = sqlite3.connect(DB_NAME)
                                cursor = conn.cursor()
                                cursor.execute(
                                    "INSERT INTO omnisync_sales (user_id, product_id, quantity_sold, total_revenue, total_cost, net_profit, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                    (active_user_id, prod_id, qty_sold, rev, cost, profit, datetime.now().isoformat())
                                )
                                cursor.execute(
                                    "UPDATE omnisync_inventory SET quantity_on_hand = quantity_on_hand - ? WHERE product_id = ?",
                                    (qty_sold, prod_id)
                                )
                                conn.commit()
                                conn.close()
                                log_event_ui(active_user_id, "omnisync_sale_recorded")
                                st.success(f"Sale recorded! Net profit generated: ${profit:,.2f}")
                                st.rerun()
                            else:
                                st.error("Quantity sold cannot exceed current stock on hand.")
                else:
                    st.info("Add products to your catalog first before logging sales.")