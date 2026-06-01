$venv = Join-Path $PSScriptRoot '..\.venv\Scripts\python.exe'
& $venv -u (Join-Path $PSScriptRoot '..\manage.py') runserver
