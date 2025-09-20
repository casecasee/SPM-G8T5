### Database Setup (MySQL)
Use phpmyadmin to import:
- File: `backend/projects/schema.sql`

Install deps (Windows):
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python projects/app.py  # http://localhost:8001
```

Install deps (macOS/Linux):
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
python3 projects/app.py  # http://localhost:8001
```