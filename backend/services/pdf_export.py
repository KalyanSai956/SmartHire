import logging

from weasyprint import HTML

logger = logging.getLogger("ats_resume_scorer")


def generate_combined_pdf(html_docs: dict[str, str]) -> bytes:
    """
    Render several HTML documents and merge them into one PDF.

    Uses WeasyPrint (pure Python + Pango) instead of headless Chromium,
    which saves ~700 MB of image size and a lot of RAM. FastAPI runs this
    in a worker thread, so blocking here is fine.
    """
    if not html_docs:
        raise ValueError("No HTML documents provided.")

    documents = []
    for name, html_str in html_docs.items():
        if not isinstance(html_str, str):
            raise TypeError(
                f"HTML document '{name}' must be a string, "
                f"got {type(html_str).__name__}"
            )
        logger.info("Generating PDF for %s (%d characters)", name, len(html_str))
        documents.append(HTML(string=html_str).render())

    pages = [page for doc in documents for page in doc.pages]
    return documents[0].copy(pages).write_pdf()
