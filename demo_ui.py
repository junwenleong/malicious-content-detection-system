import streamlit as st
import requests
import pandas as pd
import io

# Page config
st.set_page_config(
    page_title="Malicious Content Detector",
    page_icon="🛡️",
    layout="wide"
)

# Sidebar
st.sidebar.title("Configuration")
API_URL = st.sidebar.text_input("API URL", "http://127.0.0.1:8000")

# Check API health
try:
    health = requests.get(f"{API_URL}/health", timeout=2)
    if health.status_code == 200:
        st.sidebar.success(f"Connected to API: {health.json()['status']}")
    else:
        st.sidebar.error("API Error")
except:
    st.sidebar.error("Could not connect to API. Make sure it's running!")

st.title("🛡️ Malicious Content Detection System")
st.markdown("""
This interface allows you to test the malicious content detection model in real-time.
The model uses **TF-IDF + Logistic Regression** to flag abusive or malicious text.
""")

tab1, tab2 = st.tabs(["Real-time Analysis", "Batch Processing"])

with tab1:
    st.header("Single Text Analysis")
    
    text_input = st.text_area("Enter text to analyze:", height=150, placeholder="Type something here...")
    
    if st.button("Analyze Text", type="primary"):
        if text_input.strip():
            with st.spinner("Analyzing..."):
                try:
                    payload = {"texts": [text_input]}
                    response = requests.post(f"{API_URL}/predict", json=payload)
                    
                    if response.status_code == 200:
                        result = response.json()["predictions"][0]
                        label = result["label"]
                        prob = result["probability_malicious"]
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if label == "MALICIOUS":
                                st.error(f"### Result: {label}")
                            else:
                                st.success(f"### Result: {label}")
                        
                        with col2:
                            st.metric("Malicious Probability", f"{prob:.2%}")
                            st.progress(prob)
                            
                        st.json(result)
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
        else:
            st.warning("Please enter some text.")

with tab2:
    st.header("Batch File Processing")
    
    uploaded_file = st.file_uploader("Upload CSV file (must contain 'text' column)", type=["csv"])
    
    if uploaded_file is not None:
        st.info("File uploaded successfully. Processing...")
        
        if st.button("Process Batch"):
            with st.spinner("Processing batch..."):
                try:
                    # Reset pointer
                    uploaded_file.seek(0)
                    files = {"file": ("upload.csv", uploaded_file, "text/csv")}
                    response = requests.post(f"{API_URL}/batch", files=files)
                    
                    if response.status_code == 200:
                        st.success("Batch processed successfully!")
                        
                        # Parse CSV response
                        result_csv = pd.read_csv(io.StringIO(response.text))
                        
                        # Display stats
                        malicious_count = len(result_csv[result_csv['label'] == 'MALICIOUS'])
                        total_count = len(result_csv)
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Total Rows", total_count)
                        m2.metric("Malicious Detected", malicious_count)
                        m3.metric("Clean", total_count - malicious_count)
                        
                        st.dataframe(result_csv, use_container_width=True)
                        
                        # Download button
                        st.download_button(
                            label="Download Results CSV",
                            data=response.text,
                            file_name="results.csv",
                            mime="text/csv"
                        )
                    else:
                        st.error(f"Batch processing failed: {response.text}")
                except Exception as e:
                    st.error(f"Error processing file: {e}")
