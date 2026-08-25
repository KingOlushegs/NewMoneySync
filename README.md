# 💸 NewMoneySync

> **Autonomous Multi-Asset Financial Operations & Settlement Engine**
> 
> *Bridging real cash (fiat), stablecoins, and cryptocurrencies for modern businesses with automated payroll dispersals, cooperative ledgers, and regulatory compliance—housed inside a dynamic sky-blue interface because we believe the sky is the starting point.*

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit Cloud](https://img.shields.io/badge/Streamlit-Cloud-red.svg)](https://streamlit.io/)
[![SQLite3](https://img.shields.io/badge/database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Overview

**NewMoneySync** is an all-in-one financial operating system designed to bridge traditional fiat cash rails, stablecoins (USDC/USDT), and decentralized cryptocurrency networks. Built for freelancers, small businesses, and corporate cooperatives, NewMoneySync automates multi-rail invoicing, multi-asset team payroll, automated tax withholding, cooperative thrift management, and government grant/intervention matchmaking.

---

## ✨ Core Features

1. **Multi-Tenant User Gateway & Onboarding:**
   * Seamless account switcher and multi-tenant registration workflow.
   * Tailored onboarding wizard mapping business objectives, legal entity classification, and turnover brackets.

2. **Multi-Asset Invoicing & Settlement Engine:**
   * Generate smart invoices supporting stablecoins (`USDC`/`USDT`), local fiat (`NGN`), bank wire/ACH (`USD`), and crypto (`BTC`/`ETH`).

3. **VASP / Blockchain Webhook Simulation:**
   * Simulate incoming mainnet crypto/stablecoin transaction hashes (`TxHash`) to automatically split funds into net payouts, tax reserves, and cooperative pools.

4. **Multi-Asset Payroll & Dispersals Engine:**
   * **Team Directory Management:** Maintain dynamic team rosters with custom roles and preferred payout rails (`USDC`, `USDT`, `NGN Fiat`, `USD Fiat`).
   * **Multi-Currency Batch Runs:** Automatically aggregate monthly compensation liabilities split across fiat and stablecoin rails.
   * **Automated Ledger Logging:** Execute payroll runs with instant double-entry accounting records, USD-equivalent summaries, and audit tracking.

5. **Corporate Cooperative & Esusu Thrift Ledger (GRP-01):**
   * Track departmental thrift contributions, micro-loans, and perform **bulk CSV imports** for large cooperative rosters.

6. **Tax & Compliance Engine (TAX-01):**
   * Dynamic tax calculations reflecting local thresholds and exemptions.

7. **Government & CBN Intervention Matchmaker (GOV-01):**
   * Algorithmic eligibility checker linking business profiles with Nigerian federal grants, single-digit loans (BOI/SMEDAN/CBN), and auto-generating official application dossiers.

8. **Live Telemetry & Cohort Analytics:**
   * Real-time tracking of user conversion, action logs, and system events.

---

## 🛠️ Tech Stack

* **Frontend & UI:** Streamlit (with custom CSS dynamic gradients and responsive dashboards)
* **Backend:** Python
* **Database:** SQLite3 with automated schema auto-migration checks (`ALTER TABLE` dynamic patching)
* **Data Processing:** Pandas

---

## ⚙️ Local Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/newmoneysync.git](https://github.com/your-username/newmoneysync.git)
   cd newmoneysync