Restore target: backend/services/job_sources

Files:
- __init__.py
- base.py
- amazon.py
- registry.py
- router.py

This reconstruction is Amazon-only and matches the current ingestion.py contract:
load_source_adapters()
fetch_jobs_for_source(source)

Copy the files into:
backend/services/job_sources/
