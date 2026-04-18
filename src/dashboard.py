import streamlit as st
import pandas as pd
import json
import os
import time

# --- CONFIGURATION ---
ST_ICON = "🛡️"
ST_PAGE_TITLE = "BioSafety Africa: Command Center"
DEPLOYMENT_LOG = "deployment/tamper_proof_log.jsonl"
ARCHIVE_FIGURE = "biosafetyafrica_figures.png"

# --- UI CONFIG (FIXED LINE) ---
st.set_page_config(page_title=ST_PAGE_TITLE, page_icon=ST_ICON, layout="wide")

st.title(f"{ST_ICON} {ST_PAGE_TITLE}")
st.markdown("---")

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛰️ System Status")
    st.success("Security Engine: 🟢 OPERATIONAL")
    st.success("Firmware Guard: 🟢 ACTIVE")
    st.info("Forensic ESM-2: 🔵 CALIBRATED")
    st.markdown("---")
    st.markdown("### 🌍 Network")
    st.write("Sovereign Nodes Syncing...")

# --- MAIN DASHBOARD ---
col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("📊 Network Architecture")
    if os.path.exists(ARCHIVE_FIGURE):
        st.image(ARCHIVE_FIGURE)
    else:
        st.info("Architecture diagram will appear here.")

with col2:
    st.subheader("🧪 Threat Intelligence")
    threat_data = {'Pathogen': ['B. anthracis', 'Ricin', 'BoNT', 'Novel', 'Ebola'], 'Count': [45, 112, 19, 3, 22]}
    st.bar_chart(pd.DataFrame(threat_data).set_index('Pathogen'))

# --- LOG FEED ---
st.markdown("---")
st.subheader("📜 Live Secure Audit Trail")

if os.path.exists(DEPLOYMENT_LOG):
    with open(DEPLOYMENT_LOG, 'r') as f:
        log_entries = [json.loads(line) for line in f]
    df = pd.DataFrame(log_entries)
    
    # Highlight BLOCKED entries
    def highlight_blocked(s):
        return ['background-color: #ff4b4b' if 'BLOCKED' in str(v) else '' for v in s]
    
    st.dataframe(df.style.apply(highlight_blocked, axis=1), use_container_width=True)
else:
    st.warning("Awaiting log data...")

# Auto-refresh every 10 seconds
time.sleep(10)
st.rerun()
