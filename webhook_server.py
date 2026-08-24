from fastapi import FastAPI, Request, HTTPException, Header
import sqlite3
from datetime import datetime
import hmac
import hashlib
import os
from dotenv import load_dotenv

# Load variables from your .env file
load_dotenv()

app = FastAPI(title="NewMoneySync Live Webhook Listener")
DB_NAME = "newmoneysync.db"

# Pull the secret dynamically from the environment variables securely
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "fallback_secret").encode()

def verify_signature(payload_bytes: bytes, signature_header: str) -> bool:
    """
    Validates the incoming HMAC-SHA256 signature from the payment gateway.
    """
    if not signature_header:
        return False
    
    # Generate expected signature using our secret key
    computed_signature = hmac.new(
        WEBHOOK_SECRET, 
        msg=payload_bytes, 
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(computed_signature, signature_header)

@app.post("/api/v1/webhook/stablecoin")
async def receive_stablecoin_webhook(
    request: Request,
    x_signature: str = Header(None, alias="X-Signature")
):
    """
    Production webhook listener for gateways like Circle or Bridge with 
    strict cryptographic signature validation.
    """
    # 1. Read raw body bytes for signature validation before consuming the stream
    body_bytes = await request.body()
    
    # 2. Enforce cryptographic signature verification for production security
    # (Comment out this block only if you are actively testing local mock requests without a header generator)
    if not verify_signature(body_bytes, x_signature):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid or missing webhook cryptographic signature.")

    payload = await request.json()
    
    # 3. Extract webhook event details (standard schema format for VASP APIs)
    event_type = payload.get("event_type") or payload.get("type")
    data = payload.get("data", {})
    
    tx_hash = data.get("transaction_hash") or data.get("id", "0x_live_mainnet_tx")
    invoice_id = data.get("metadata", {}).get("invoice_id") or payload.get("invoice_id")
    
    if not invoice_id:
        raise HTTPException(status_code=400, detail="Missing invoice reference in webhook payload.")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 4. Fetch invoice, user details, and business profile for tax rules
    cursor.execute("SELECT user_id, amount, status FROM invoices WHERE invoice_id = ?", (invoice_id,))
    inv_row = cursor.fetchone()
    
    if not inv_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found.")
        
    user_id, amt, current_status = inv_row
    
    if current_status == "settled":
        conn.close()
        return {"status": "success", "message": "Invoice was already marked as settled."}

    # --- AUTOMATED TAX SPLITTING ENGINE ---
    # Example calculation: Applying standard compliance split (e.g., 7.5% VAT / applicable withholding calculation)
    tax_rate = 0.075 
    calculated_tax = round(float(amt) * tax_rate, 2)
    net_settlement = round(float(amt) - calculated_tax, 2)

    # 5. Update invoice to settled with real mainnet hash and net/tax figures
    cursor.execute(
        """UPDATE invoices 
           SET status = 'settled', payment_tx_hash = ?, tax_deducted = ?, net_amount = ? 
           WHERE invoice_id = ?""", 
        (tx_hash, calculated_tax, net_settlement, invoice_id)
    )
    
    # 6. Record entry into the tax ledger / compliance liability table
    cursor.execute(
        """INSERT INTO tax_ledger (user_id, invoice_id, gross_amount, tax_liability, timestamp) 
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, invoice_id, amt, calculated_tax, datetime.now().isoformat())
    )

    # 7. Log telemetry event
    now = datetime.now().isoformat()
    cohort_week = datetime.now().strftime("%Y-W%V")
    cursor.execute(
        "INSERT INTO telemetry_events (user_id, event_name, timestamp, cohort_week) VALUES (?, ?, ?, ?)",
        (user_id, "live_webhook_invoice_settled_with_tax", now, cohort_week)
    )
    
    conn.commit()
    conn.close()

    return {
        "status": "success", 
        "message": f"Invoice #{invoice_id} successfully settled via verified cryptographic webhook!",
        "tx_hash": tx_hash
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("webhook_server:app", host="127.0.0.1", port=8000, reload=True)