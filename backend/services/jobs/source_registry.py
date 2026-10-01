from __future__ import annotations

from backend.services.jobs.company_source_registry import (
    COMPANY_SOURCE_CONFIGS,
    CompanySourceConfig,
    get_company_source_config,
    get_company_source_configs,
    get_enabled_company_source_configs,
    is_legacy_provider,
    is_target_company,
)


def get_enabled_sources() -> list[CompanySourceConfig]:
    return get_enabled_company_source_configs()


def get_all_sources() -> list[CompanySourceConfig]:
    return get_company_source_configs()


def get_source_by_company(
    company_slug: str,
) -> CompanySourceConfig | None:
    return get_company_source_config(
        company_slug
    )


def is_source_enabled(
    company_slug: str,
) -> bool:
    source = get_company_source_config(
        company_slug
    )

    return (
        source is not None
        and source.enabled
    )


def is_provider_allowed(
    provider: str,
) -> bool:
    return not is_legacy_provider(
        provider
    )