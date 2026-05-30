# api-test-gameloft

## Installation

This project uses a virtual environment with standard Windows Python (CPython 3.13).

```powershell
# Activate the virtual environment
.\.venv\Scripts\activate

# Install dependencies (already installed if you follow the setup)
pip install fastapi uvicorn
```

## Running the API

```powershell
uvicorn main:app --reload
```