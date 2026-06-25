from .common import extract_job_posting


def extract_from_markup(row, markup):
    return extract_job_posting(
        row,
        markup,
        portal_name="Computrabajo",
        source_name="computrabajo",
        selectors=(
            r'<div[^>]+class=["\'][^"\']*(?:job|description|descripcion)[^"\']*["\'][^>]*>(.*?)</div>',
            r'<section[^>]+class=["\'][^"\']*(?:job|description|descripcion)[^"\']*["\'][^>]*>(.*?)</section>',
        ),
    )
