SMART JOB MATCHER — SETUP (WINDOWS)

1. Install Python if it is not already installed.
2. Open the folder containing app.py in VS Code.
3. Open Terminal > New Terminal.
4. Run:
   python -m pip install -r requirements.txt
5. Start the app:
   python -m streamlit run app.py
6. Streamlit will show a local address (usually http://localhost:8501). Open it in your browser.

Notes:
- The app uses the JobsForce India public jobs API.
- Local listings are only shown when the returned city and state match the values you entered.
- If the API has no verified listings for a city, the app will show a no-results message rather than pretending jobs from another city are local.
- Remote jobs are shown in a separate tab.
- Skill match percentages are keyword-based estimates.
