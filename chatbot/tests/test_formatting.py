from secim_chatbot.formatting import normalize_question, tr_lower, tr_number


def test_tr_number():
    assert tr_number(19127097) == "19.127.097"
    assert tr_number(35.23) == "35,23"
    assert tr_number(1234.5) == "1.234,50"
    assert tr_number("CHP") == "CHP"


def test_turkish_lowercase():
    assert tr_lower("İSTANBUL") == "istanbul"
    assert tr_lower("IĞDIR") == "ığdır"
    assert normalize_question("Kadıköy'de HAYIR oranı?") == "kadıköy de hayır oranı"
