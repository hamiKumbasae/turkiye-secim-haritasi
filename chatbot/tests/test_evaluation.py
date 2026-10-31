from secim_chatbot.evaluation import results_match


def test_exact_match():
    assert results_match([["CHP", 31]], [["CHP", 31]])


def test_numeric_and_case_normalisation():
    assert results_match([["İstanbul", 35.23]], [["istanbul", 35.2299]])
    assert results_match([[268]], [["268"]])


def test_extra_columns_in_prediction_are_allowed_any_order():
    assert results_match([["CHP", 31]], [[2023, 31, "CHP"]])


def test_missing_column_fails():
    assert not results_match([["CHP", 31]], [["CHP"]])


def test_wrong_value_or_row_count_fails():
    assert not results_match([["CHP", 31]], [["CHP", 30]])
    assert not results_match([["CHP", 31]], [["CHP", 31], ["AKP", 1]])


def test_unordered_vs_ordered():
    gold = [["a", 3], ["b", 2], ["c", 1]]
    pred = [["b", 2], ["a", 3], ["c", 1]]
    assert results_match(gold, pred, ordered=False)
    assert not results_match(gold, pred, ordered=True)


def test_ordered_tolerates_ties_in_sort_key():
    gold = [["Düzce", 92.26], ["Bilecik", 91.97], ["Kütahya", 91.97]]
    pred = [["Düzce", 92.26], ["Kütahya", 91.97], ["Bilecik", 91.97]]
    assert results_match(gold, pred, ordered=True)


def test_empty_results():
    assert results_match([], [])
    assert not results_match([], [["x"]])
