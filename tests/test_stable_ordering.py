from botjobs.app import sort_result_rows


def test_equal_scores_have_stable_order_independent_of_input():
    alpha = {"score": 90, "empresa": "Alpha", "nombre_de_la_vacante": "Developer", "url": "https://example.test/2"}
    beta = {"score": 90, "empresa": "Beta", "nombre_de_la_vacante": "Developer", "url": "https://example.test/1"}

    first = sort_result_rows([beta, alpha])
    second = sort_result_rows([alpha, beta])

    assert [row["empresa"] for row in first] == ["Alpha", "Beta"]
    assert first == second
