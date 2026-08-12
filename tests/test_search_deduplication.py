from botjobs.search import canonical_job_url, dedupe_rows


def test_canonical_url_removes_tracking_and_fragment_but_keeps_job_identity():
    first = "HTTPS://MX.INDEED.COM/viewjob?jk=abc&utm_source=email&from=app#details"
    second = "https://mx.indeed.com/viewjob?from=search&jk=abc"

    assert canonical_job_url(first) == "https://mx.indeed.com/viewjob?jk=abc"
    assert canonical_job_url(first) == canonical_job_url(second)


def test_dedupe_rows_uses_canonical_url_and_preserves_first_row():
    rows = [
        {"url": "https://www.linkedin.com/jobs/view/123?trackingId=one", "titulo": "Primera"},
        {"url": "https://linkedin.com/jobs/view/123?trk=feed", "titulo": "Duplicada"},
    ]

    unique = dedupe_rows(rows, max_results=10)

    assert len(unique) == 1
    assert unique[0]["titulo"] == "Primera"
    assert unique[0]["url"] == "https://linkedin.com/jobs/view/123"
