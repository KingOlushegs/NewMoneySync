import sqlite3
from datetime import datetime

DB_NAME = "newmoneysync.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            tier TEXT DEFAULT 'paid',
            entity_type TEXT DEFAULT 'Freelancer',
            annual_turnover REAL DEFAULT 5000.0,
            tax_bracket_rate REAL DEFAULT 0.0,
            coop_split_rate REAL DEFAULT 5.0,
            traffic_source TEXT,
            signup_date TEXT,
            cohort_week TEXT
        )
    """)

    # 2. Invoices Table (Updated with Tax & Net Breakdown)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            client_name TEXT,
            amount REAL,
            asset_type TEXT,
            status TEXT DEFAULT 'pending',
            payment_tx_hash TEXT,
            tax_deducted REAL DEFAULT 0.0,
            net_amount REAL DEFAULT 0.0,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)

    # 3. Telemetry Event Log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_name TEXT,
            timestamp TEXT,
            cohort_week TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)

    # 4. Cooperative Members Table (For Esusu/Thrift Collections)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cooperative_members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            member_name TEXT NOT NULL,
            email TEXT,
            department TEXT,
            monthly_contrib REAL DEFAULT 0.0,
            joined_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    # 5. Intervention Matches Table (For GOV-01 Matchmaker)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS intervention_matches (
            match_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            program_name TEXT,
            fund_type TEXT,
            max_amount TEXT,
            interest_rate TEXT,
            eligibility_status TEXT,
            matched_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    # 6. Merchant Risk & Rolling Reserves Table (For Chargeback & Fraud Protection)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS merchant_risks (
            risk_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            rolling_reserve_balance REAL DEFAULT 0.0,
            circuit_breaker_status TEXT DEFAULT 'ACTIVE',
            risk_score REAL DEFAULT 0.0,
            last_updated TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)

    # 7. Tax Ledger Table (For Compliance Liabilities & Audit Tracking)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tax_ledger (
            tax_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            invoice_id INTEGER,
            gross_amount REAL,
            tax_liability REAL,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (invoice_id) REFERENCES invoices (invoice_id)
        )
    """)

    # 8. Cooperative Ledger Table (For Esusu/Thrift Pool Contributions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cooperative_ledger (
            contribution_id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT,
            member_id INTEGER,
            amount REAL,
            reference TEXT,
            timestamp TEXT,
            status TEXT DEFAULT 'verified',
            FOREIGN KEY (member_id) REFERENCES cooperative_members (member_id)
        )
    """)

    conn.commit()
    conn.close()
    print("Database schema updated with tax tracking and compliance tables!")

if __name__ == "__main__":
    init_db()