# Run TERRATREND on Windows

## 1. Install Python
Use Python 3.11 (64-bit). During installation, enable the Python launcher if offered.

Check in PowerShell:

```powershell
py -3.11 --version
```

## 2. Extract the project
Extract `TERRATREND_MVP_v0_1.zip`. Open PowerShell in the extracted `TERRATREND_MVP` folder.

## 3. Create an isolated environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 4. Start the app

```powershell
streamlit run app.py
```

Open `http://localhost:8501`.

## 5. First live test
Select Lahore, Karachi and Skardu; select T2M; use 1981–2025; click **Run NASA analysis**. The first request needs an internet connection to NASA POWER. Subsequent identical requests are cached for 24 hours.

## Troubleshooting
- `ModuleNotFoundError`: activate the environment and rerun `pip install -r requirements.txt`.
- NASA POWER HTTP error: wait and retry; check the parameter, dates and internet connection.
- No annual observations: verify that the selected parameter returned 12 monthly values per year for the selected period.
- Streamlit port already in use: run `streamlit run app.py --server.port 8502`.

Do not upload `.venv`, secrets, or large raw datasets to GitHub.
