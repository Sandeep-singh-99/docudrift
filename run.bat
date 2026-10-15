@echo off
echo Starting DocuDrift Sentinel...
call .\venv\Scripts\activate
streamlit run ui\app.py
pause
