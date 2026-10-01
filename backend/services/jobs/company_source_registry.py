from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompanySourceConfig:
    company_slug: str
    provider: str
    source_type: str
    enabled: bool
    source_url: str
    api_url: str | None = None
    board_token: str | None = None
    provider_config: dict | None = None


COMPANY_SOURCE_CONFIGS = (
    CompanySourceConfig("amazon", "amazon", "official_portal", True, "https://www.amazon.jobs/en/search?country=IND&loc_query=India", provider_config={"country": "IND", "location": "India", "result_limit": 100}),
    CompanySourceConfig("google", "google", "official_portal", True, "https://www.google.com/about/careers/applications/jobs/results/?location=India&hl=en", provider_config={"strategy": "google"}),
    CompanySourceConfig("microsoft", "microsoft", "official_portal", True, "https://careers.microsoft.com/v2/global/en/locations/india.html", provider_config={"strategy": "microsoft"}),
    CompanySourceConfig("accenture", "accenture", "official_portal", True, "https://www.accenture.com/in-en/careers/jobdetails?id=ATCI-5308518-S1945157_en", provider_config={"strategy": "accenture"}),
    CompanySourceConfig("cognizant", "cognizant", "official_portal", True, "https://careers.cognizant.com/india-en/jobs/", provider_config={"strategy": "cognizant"}),
    CompanySourceConfig("deloitte", "deloitte", "official_portal", True, "https://southasiacareers.deloitte.com/go/Deloitte-India/718244?q=&sortColumn=sort_title&sortDirection=asc", provider_config={"strategy": "deloitte"}),
)


LEGACY_PROVIDERS = frozenset({"greenhouse", "lever", "drivetrain"})


def get_company_source_configs() -> list[CompanySourceConfig]:
    return list(COMPANY_SOURCE_CONFIGS)


def get_enabled_company_source_configs() -> list[CompanySourceConfig]:
    return [config for config in COMPANY_SOURCE_CONFIGS if config.enabled]


def get_company_source_config(company_slug: str) -> CompanySourceConfig | None:
    normalized_slug = company_slug.strip().lower()
    for config in COMPANY_SOURCE_CONFIGS:
        if config.company_slug == normalized_slug:
            return config
    return None


def is_target_company(company_slug: str) -> bool:
    return get_company_source_config(company_slug) is not None


def is_legacy_provider(provider: str) -> bool:
    return provider.strip().lower() in LEGACY_PROVIDERS
