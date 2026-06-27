# AddressRefine

AddressRefine is a server-rendered FastAPI web app for cleaning up messy address lists: upload a CSV, map its columns to address fields (zip, street, city, country), run a fuzzy-matching algorithm to surface likely duplicate addresses, then review and merge the candidates you confirm — all without a database, using simple in-memory, cookie-keyed session state.

## Setup (Windows / PowerShell)

```powershell
# Create a virtual environment
py -3.11 -m venv .venv

# Activate it
.venv\Scripts\Activate.ps1

# Install dependencies (includes dev tools: pytest, httpx, ruff)
pip install -r requirements-dev.txt

# Run the app
uvicorn app.main:app --reload

# Run tests
pytest -q

# Lint
ruff check .
```

Once running, open http://127.0.0.1:8000/ in a browser.
