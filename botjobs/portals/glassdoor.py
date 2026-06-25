from .common import extract_job_posting


def extract_from_markup(row, markup):
    return extract_job_posting(
        row,
        markup,
        portal_name="Glassdoor",
        source_name="glassdoor",
        selectors=(
            r'<div[^>]+id=["\']JobDescriptionContainer["\'][^>]*>(.*?)</div>',
            r'<div[^>]+class=["\'][^"\']*(?:jobDescription|description)[^"\']*["\'][^>]*>(.*?)</div>',
        ),
    )
