from .common import extract_job_posting


def extract_from_markup(row, markup):
    return extract_job_posting(
        row,
        markup,
        portal_name="Indeed",
        source_name="indeed",
        selectors=(
            r'<div[^>]+id=["\']jobDescriptionText["\'][^>]*>(.*?)</div>',
            r'<section[^>]+id=["\']jobDescriptionText["\'][^>]*>(.*?)</section>',
        ),
    )