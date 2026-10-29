import os
import pandas as pd
import streamlit as st
from supabase import create_client
from dotenv import load_dotenv
from engine.sam_parser import load_and_aggregate_sam

load_dotenv()

def get_supabase():
    # Try Streamlit secrets first (for cloud deployment)
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        # Fallback to local .env
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
    if not url or not key:
        return None
    return create_client(url, key)

def load_twin_data():
    """Load the A matrix, VA ratios, and sector names from the SAM."""
    A, va, _ = load_and_aggregate_sam()
    return A, va, A.index.tolist()
