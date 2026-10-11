# Cura AI - Personal Health Copilot

Upload a prescription or lab report (photo/PDF). The app extracts medicines, dosages, test values and
dates, explains them in simple language (English, Hindi, Telugu, Tamil, Kannada), saves them to a
timeline, and exports FHIR-style records with a mock ABHA ID.

## Run Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the application:
   ```bash
   streamlit run app.py
   ```
3. Open `http://localhost:8501` in your browser.

## Configuration
Add your Gemini API key inside `.streamlit/secrets.toml` or directly into the sidebar at runtime.
