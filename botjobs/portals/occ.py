from .common import extract_job_posting


def extract_from_markup(row, markup):
    return extract_job_posting(
        row,
        markup,
        portal_name="OCC",
        source_name="occ",
        selectors=(
            r'<div[^>]+class=["\'][^"\']*(?:job|description|descripcion|detalle)[^"\']*["\'][^>]*>(.*?)</div>',
            r'<section[^>]+class=["\'][^"\']*(?:job|description|descripcion|detalle)[^"\']*["\'][^>]*>(.*?)</section>',
        ),
    )
