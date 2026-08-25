import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

DB_NAME = "newmoneysync.db"

# --- DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Core Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
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

# --- SEED A DEFAULT TEST USER IF NONE EXISTS ---
users = run_query("SELECT user_id, username, entity_type, annual_turnover, coop_split_rate, onboarding_count FROM users")
if not users:
    signup_date = datetime.now().isoformat()
    cohort_week = datetime.now().strftime("%Y-W%V")
    run_query(
        """INSERT INTO users (username, email, tier, entity_type, annual_turnover, tax_bracket_rate, coop_split_rate, traffic_source, signup_date, cohort_week, primary_intent, onboarding_complete) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("Olu-Shegs", "olu@newmoneysync.com", "paid", "Freelancer", 12000.0, 7.5, 5.0, "utm_google", signup_date, cohort_week, "Global Inflows & Settlements", 0),
        fetch=False
    )
    users = run_query("SELECT user_id, username, entity_type, annual_turnover, coop_split_rate, onboarding_complete FROM users")

active_user_id = users[0][0]
active_username = users[0][1]
onboarding_status = users[0][5]

# ==========================================
# ONBOARDING WIZARD SCREEN (IF NOT COMPLETE)
# ==========================================
if onboarding_status == 0:
    st.title("🚀 Welcome to NewMoneySync")
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
        entity_class = st.selectbox("Entity Type", ["Freelancer", "Small Business (< ₦100M Turnover)", "Registered Corporation", "Cooperative Society"])
        annual_rev = st.number_input("Estimated Annual Turnover ($)", min_value=0.0, value=15000.0)
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
    # --- SIDEBAR NAVIGATION (UNLOCKED AFTER ONBOARDING) ---
    st.sidebar.title("NewMoneySync 💸")
    st.sidebar.caption("Autonomous Settlement & Compliance")

    menu = st.sidebar.radio(
        "Navigation", 
        [
            "Dashboard & Telemetry", 
            "Invoicing & Stablecoin Settlement", 
            "Webhook Simulation (Auto-Pay)",
            "Payroll & Dispersals",
            "User Settings & Automation Rules",
            "Cooperative Ledger (GRP-01)",
            "Tax & Compliance Engine",
            "CBN Intervention Matchmaker (GOV-01)"
        ]
    )

    st.sidebar.markdown(f"**Active User:** {active_username} (ID: {active_user_id})")

    # ==========================================
    # 1. DASHBOARD & TELEMETRY VIEW
    # ==========================================
    if menu == "Dashboard & Telemetry":
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

        df_users = pd.read_sql("SELECT * FROM users", sqlite3.connect(DB_NAME))
        df_events = pd.read_sql("SELECT * FROM telemetry_events", sqlite3.connect(DB_NAME))
        df_invoices = pd.read_sql("SELECT * FROM invoices", sqlite3.connect(DB_NAME))

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
                st.dataframe(df_users[['user_id', 'username', 'traffic_source', 'cohort_week', 'tier']], use_container_width=True)
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
        user_info = run_query("SELECT entity_type, annual_turnover, tax_bracket_rate, coop_split_rate FROM users WHERE user_id = ?", (active_user_id,))[0]
        
        with st.form("settings_form"):
            entity_type = st.selectbox("Entity Classification", ["Freelancer", "Small Business (< ₦100M Turnover)", "Registered Corporation"], index=["Freelancer", "Small Business (< ₦100M Turnover)", "Registered Corporation"].index(user_info[0]))
            annual_turnover = st.number_input("Estimated Annual Revenue ($)", min_value=0.0, value=user_info[1])
            coop_split_rate = st.slider("Cooperative Pool Allocation (%)", min_value=0.0, max_value=25.0, value=user_info[3], step=0.5)
            
            if st.form_submit_button("Save Automation Rules"):
                calculated_tax = 0.0 if entity_type == "Small Business (< ₦100M Turnover)" and annual_turnover <= 65000 else 7.5
                run_query("UPDATE users SET entity_type = ?, annual_turnover = ?, tax_bracket_rate = ?, coop_split_rate = ? WHERE user_id = ?", 
                          (entity_type, annual_turnover, calculated_tax, coop_split_rate, active_user_id), fetch=False)
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

        user_row = run_query("SELECT username, entity_type, annual_turnover FROM users WHERE user_id = ?", (active_user_id,))[0]
        u_name, entity_type, annual_turnover = user_row

        st.info(f"Analyzing profile for **{u_name}** | Entity: **{entity_type}** | Est. Annual Revenue: **${annual_turnover:,.2f}**")

        programs = [
            {
                "name": "FGN/BOI N75M MSME Intervention Fund",
                "type": "Low-Interest Loan (9% P.A.)",
                "max_amount": "₦1,000,000 (~$1,200)",
                "interest": "9% per annum",
                "eligibility_check": lambda e, rev: True,
                "description": "Targeted support to reduce production costs and support working capital for small businesses."
            },
            {
                "name": "BOI Guaranteed Loans for Women Entrepreneurs",
                "type": "Concessionary Loan & Grant",
                "max_amount": "₦10,000,000 (~$12,000)",
                "interest": "Single-digit subsidized",
                "eligibility_check": lambda e, rev: True,
                "description": "Empowering women-owned businesses with affordable financing and capacity building."
            },
            {
                "name": "SMEDAN National Business Skills & Matching Grant",
                "type": "Federal Grant & Equipment Support",
                "max_amount": "₦500,000 Direct Grant",
                "interest": "0% (Non-repayable grant)",
                "eligibility_check": lambda e, rev: rev <= 50000.0,
                "description": "Designed to scale micro-enterprises, provide shared facility access, and equip growing digital/industrial startups."
            },
            {
                "name": "CBN Real Sector Support Facility (RSSF / 100 for 100 PPP)",
                "type": "Long-Term Industrial Financing",
                "max_amount": "₦5,000,000,000",
                "interest": "5% - 9% per annum",
                "eligibility_check": lambda e, rev: rev >= 20000.0,
                "description": "Targeted at large scale manufacturing, tech infrastructure, agro-processing, and export-driven production."
            }
        ]

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