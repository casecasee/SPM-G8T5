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

### Migrations

After pulling latest, run this migration to add the optional project due date column:

Windows PowerShell:

```
mysql -u root -p SPM < backend\projects\migrations\001_add_due_date.sql
```

macOS/Linux:

```
mysql -u root -p SPM < backend/projects/migrations/001_add_due_date.sql
```

Then restart the service.