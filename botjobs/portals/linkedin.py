from .common import extract_job_posting


def extract_from_markup(row, markup):
    return extract_job_posting(
        row,
        markup,
        portal_name="LinkedIn",
        source_name="linkedin",
        selectors=(
            r'<div[^>]+class=["\'][^"\']*show-more-less-html__markup[^"\']*["\'][^>]*>(.*?)</div>',
            r'<section[^>]+class=["\'][^"\']*(?:description|jobs-description)[^"\']*["\'][^>]*>(.*?)</section>',
        ),
    )
