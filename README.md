# softitglobal_clone_backend
Django REST API backend for SoftITGlobal platform. Handles authentication, business logic, and data management for the Next.js frontend via RESTful APIs.

Stack
-----

- Backend framework: Django 5
- API layer: Django REST Framework (DRF)
- Frontend (paired project): Next.js
- Database (current local setup): SQLite (`db.sqlite3`)
- Language/runtime: Python 3.13

Quickstart
----------

- Create and activate the Python virtual environment:

```powershell
python -m venv .venv
.\\venv\\Scripts\\Activate.ps1   # PowerShell
```

- Install dependencies:

```powershell
.venv\\Scripts\\python.exe -m pip install -r requirements.txt
```

- Run the dev server (use the script to ensure the venv interpreter is used):

```powershell
scripts\\runserver.ps1
```

If you prefer manual commands, activate the venv then run `python manage.py runserver`.
