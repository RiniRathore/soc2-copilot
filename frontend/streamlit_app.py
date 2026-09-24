"""
Run with:  streamlit run frontend/streamlit_app.py

Deliberately basic -- one page, one button, one table, plus a settings
panel for credentials. All the actual work happens in the FastAPI
pipeline; this is just a demo-friendly window into it.
"""
import os

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="SOC 2 Copilot", layout="wide")
st.title("SOC 2 Copilot")
st.caption("Scans infra config against SOC 2 + CIS controls, verifies its own findings, opens a PR.")

API_URL = "http://localhost:8000"
# Same API_KEY the backend requires -- both processes read it from the
# same .env, since this frontend and the backend are meant to be run by
# the same operator (see require_api_key in app/main.py).
API_HEADERS = {"X-API-Key": os.getenv("API_KEY", "")}

if not API_HEADERS["X-API-Key"]:
    st.error("API_KEY is not set in .env -- the backend will reject every request. Set it and restart.")

# --- Settings panel ---------------------------------------------------
with st.sidebar:
    st.header("Settings")
    st.caption(
        "Credentials are held in server-side memory only for this "
        "session -- never written to disk. Leave a field blank to keep "
        "whatever's already set in .env."
    )

    with st.form("settings_form"):
        st.subheader("Gemini")
        gemini_api_key = st.text_input("Gemini API key", type="password")

        st.subheader("GitHub")
        github_token = st.text_input("GitHub token", type="password")
        github_repo = st.text_input("GitHub repo", placeholder="your-org/your-demo-repo")

        st.subheader("AWS (only needed for live_api scans)")
        aws_access_key_id = st.text_input("AWS access key ID", type="password")
        aws_secret_access_key = st.text_input("AWS secret access key", type="password")
        aws_region = st.text_input("AWS region", placeholder="ap-south-1")

        st.subheader("GCP (not yet wired into scanning -- reserved)")
        gcp_project_id = st.text_input("GCP project ID")
        gcp_service_account_json = st.text_area(
            "GCP service account JSON", height=80,
            help="Paste the JSON key contents directly, not a file path.",
        )

        submitted = st.form_submit_button("Save settings")

    if submitted:
        payload = {
            "gemini_api_key": gemini_api_key or None,
            "github_token": github_token or None,
            "github_repo": github_repo or None,
            "aws_access_key_id": aws_access_key_id or None,
            "aws_secret_access_key": aws_secret_access_key or None,
            "aws_region": aws_region or None,
            "gcp_project_id": gcp_project_id or None,
            "gcp_service_account_json": gcp_service_account_json or None,
        }
        try:
            resp = requests.post(f"{API_URL}/configure", json=payload, headers=API_HEADERS, timeout=10)
            resp.raise_for_status()
            configured = resp.json()["configured"]
            st.success(f"Saved: {', '.join(configured) if configured else '(nothing set)'}")
        except Exception as e:
            st.error(f"Couldn't save settings: {e}")

    # Show what's currently active without ever displaying secret values
    try:
        status = requests.get(f"{API_URL}/configure", headers=API_HEADERS, timeout=5).json()
        if status["configured"]:
            st.caption(f"Currently set: {', '.join(status['configured'])}")
        else:
            st.caption("Nothing set yet -- using .env defaults where available.")
    except Exception:
        st.caption("Backend not reachable yet.")

# --- Main scan panel ----------------------------------------------------
col1, col2 = st.columns([1, 3])
with col1:
    source = st.radio("Input source", ["terraform", "live_api"], index=0)
    open_pr = st.checkbox("Open GitHub PR for confirmed findings", value=True)
    run_clicked = st.button("Run scan", type="primary")

if run_clicked:
    try:
        with st.spinner("Scanning... (a full scan makes many sequential Gemini calls and can take several minutes on the free tier, longer if Gemini is rate-limiting or overloaded)"):
            payload = {"source": source, "open_pr": open_pr}
            response = requests.post(f"{API_URL}/scan", json=payload, headers=API_HEADERS, timeout=1200)
            response.raise_for_status()
            result = response.json()
    except Exception as e:
        st.error(f"Scan failed: {e}")
        result = None

    if result:
        findings = result["findings"]
        st.success(f"Scan complete — {len(findings)} confirmed violation(s)")

        if findings:
            df = pd.DataFrame(findings)[
                ["resource_type", "resource_name", "framework", "control_id",
                 "severity", "verification_status", "reasoning"]
            ]
            st.dataframe(df, use_container_width=True)

        if result.get("pr_url"):
            st.markdown(f"**[Open the generated PR]({result['pr_url']})**")
        elif result.get("pr_error"):
            st.warning(f"Findings are confirmed above, but opening the PR failed: {result['pr_error']}")

        st.caption("Full reasoning traces (retrieval → reasoning → self-check) are logged to Langfuse for this run.")
else:
    st.info("Click 'Run scan' to check the seed infra against SOC 2 + CIS controls.")
