from backend.services.job_sources.amazon import AmazonAdapter
from backend.services.job_sources.base import JobSourceAdapter, JobSourceJob
from backend.services.job_sources.registry import load_source_adapters
from backend.services.job_sources.router import fetch_jobs_for_source, get_adapter, register_adapter, registered_providers
