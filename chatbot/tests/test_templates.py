"""Template layer: slot resolution, confident-or-fall-through, safety, and known answers on the DB."""
import json
from pathlib import Path

import pytest
import yaml
from conftest import real_db_or_skip

from secim_chatbot.entities import default_index
from secim_chatbot.evaluation import results_match
from secim_chatbot.llm import Turn
from secim_chatbot.safety import validate_sql
from secim_chatbot.templates import NoMatch, TemplateEngine, parse, resolve_elections

ROOT = Path(__file__).resolve().parent.parent
IDX = default_index()
ENGINE = TemplateEngine(index=IDX)
BANK = {b["id"]: b for b in yaml.safe_load((ROOT / "eval" / "soru_bankasi.yaml").read_text(encoding="utf-8"))}
GOLD = {g["id"]: g for g in yaml.safe_load((ROOT / "eval" / "gold.yaml").read_text(encoding="utf-8"))}
SNAP = {**json.loads((ROOT / "eval" / "soru_bankasi_results.json").read_text(encoding="utf-8")),
        **json.loads((ROOT / "eval" / "gold_results.json").read_text(encoding="utf-8"))}


def kods(q):
    return [e.kod for e in resolve_elections(parse(q, IDX), IDX)]


# ---------------------------------------------------------------------------- elections
@pytest.mark.parametrize("q,expected", [
    ("2023'te CHP kaç oy aldı?", ["2023"]),                                 # party → general election
    ("2023 ikinci turda Kılıçdaroğlu", ["2023cb2tur"]),
    ("ikinci turda Erdoğan kaç oy aldı", ["2023cb2tur"]),                   # documented default
    ("14 Mayıs'ta CHP", ["2023"]), ("14 Mayıs'ta Erdoğan", ["2023cb1tur"]),
    ("91 seçiminde birinci parti", ["1991"]), ("83 seçiminde ANAP", ["1983"]),
    ("2019'da CHP İstanbul'da", ["2019yerel"]),                             # only a local election that year
    ("2018 cumhurbaşkanlığı seçiminde", ["2018cb"]),
    ("2017 referandumunda Hayır", ["2017referandum"]),
    ("1 Kasım 2015 seçiminde", ["2015Kasim"]), ("Haziran 2015'te MHP", ["2015Haziran"]),
    ("2023te chp", ["2023"]),                                              # year with suffix, no apostrophe
    ("2018'den 2023'e AK Parti", ["2018", "2023"]),
])
def test_election_resolution(q, expected):
    assert kods(q) == expected


@pytest.mark.parametrize("q", [
    "2015 seçiminde CHP kaç oy aldı?",          # June or November
    "2023'te Erdoğan yüzde kaç aldı?",          # first or second round
    "2019 genel seçiminde CHP",                 # no such election
    "2023 cumhurbaşkanlığı yerel seçimi",       # contradictory type
])
def test_ambiguous_or_impossible_elections_raise(q):
    with pytest.raises(NoMatch):
        resolve_elections(parse(q, IDX), IDX)


# ---------------------------------------------------------------------------- fall through
@pytest.mark.parametrize("q", [
    "Yenişehir'de 2019'da kim kazandı?",                       # district in 3 provinces
    "Gölbaşı'nda 2024'te kim kazandı?",                        # Ankara or Adıyaman
    "CHP İzmir'de 2023'te birinci oldu mu?",                   # yes/no question
    "AK Parti 2023'te hangi illerden hiç vekil çıkaramadı?",   # negation
    "2023'te Cumhur İttifakı kaç oy aldı?",                    # alliance
    "AK Parti 2023'te kaç ilde ikinci oldu?",                  # other rank than first
    "Finanskent mahallesinde 2023'te AK Parti yüzde kaç aldı?",  # unknown proper noun
    "Ankara'da 2024 yerel seçiminde Mansur Yavaş yüzde kaç aldı?",
    "2015'te CHP kaç oy aldı?",
    "Ege'de 2023'te CHP'nin oyu",                              # region
    "Erdoğan ikinci turda oyunu en çok hangi 5 ilde artırdı?",  # change without two elections
    "2002 seçiminde yüzde 10 barajını hangi partiler geçebildi?",
    "Meclisteki sandalye sayısı 1983'te kaçtı, şimdi kaç?",
    "Galatasaray kaç şampiyonluk kazandı?",
    "2023'te Çankaya'da AK Parti'nin oyu ile Keçiören'deki oyu",
])
def test_unclear_questions_fall_through(q):
    assert ENGINE.match(q) is None


@pytest.mark.parametrize("q", [
    "2023'te İstanbul'dan seçilen milletvekillerinin isimleri neler?",
    "Kadıköy'de sandık bazında sonuçlar",
    "2024 yerel seçimlerinde belediye meclisi oyları",
    "Seçim barajı neden yüzde 7'ye indirildi?",
    "1946 seçiminde DP kaç oy aldı?",
    "Gençler kime oy verdi?",
    "2023 seçiminde kaç oy geçersiz sayıldı?",
])
def test_data_gaps_are_refused_by_rule(q):
    m = ENGINE.match(q)
    assert m is not None and m.template == "veri-yok" and m.refusal and m.sql is None


# ---------------------------------------------------------------------------- SQL shape
QUESTIONS = {
    "birim-sonucu": ["Ankara'da 2018 milletvekili seçiminde birinci parti hangisiydi?",
                     "Sultanbeyli 2024 yerel seçim sonucu, ilk üç", "Esenyurt'ta 14 Mayıs'ta Erdoğan yüzde kaç aldı?",
                     "1999 genel seçimini hangi parti kazandı?"],
    "ulusal-oy": ["2023 genel seçiminde AK Parti Türkiye genelinde kaç oy aldı?",
                  "2017 referandumunda yurt içinde Evet oranı kaç çıktı?"],
    "kac-yerde-birinci": ["1995'te Refah Partisi kaç ilde birinci çıkmıştı?",
                          "CHP 2024'te kaç büyükşehiri kazandı?"],
    "en-yuksek-dusuk": ["Kılıçdaroğlu'nun ikinci turda en yüksek oy aldığı 5 ilçe",
                        "AK Parti 2023'te hangi illerde yüzde 50'nin üstüne çıktı?"],
    "nerede-birinci": ["2018 seçiminde HDP'nin birinci olduğu iller hangileri?"],
    "vekil": ["HDP Haziran 2015'te kaç vekil çıkarmıştı?", "2023 genel seçiminde partiler kaçar milletvekili çıkardı?"],
    "fark": ["2023 genel seçiminde AK Parti ile CHP arasında kaç oy fark vardı?",
             "Gaziosmanpaşa'da 2024'te kazanan ile ikinci arasındaki fark"],
    "katilim": ["Ümraniye'de 2024 yerel seçimde katılım yüzde kaçtı?",
                "2023 genel seçiminde katılımın en yüksek olduğu 5 il hangileri?"],
    "secmen-sayisi": ["1950'de en çok seçmeni olan il hangisiydi?"],
    "zaman-serisi-oran": ["Kadıköy'de CHP'nin genel seçimlerdeki oyu 2002'den bu yana"],
    "zaman-serisi-kazanan": ["1950'den bu yana her genel seçimde Ankara'da hangi parti birinci oldu?"],
    "oy-degisimi": ["AK Parti'nin oyu 2018'den 2023'e en çok hangi 5 ilde düştü?",
                    "AK Parti 2002'den 2007'ye kaç oy artırdı?"],
}


@pytest.mark.parametrize("template,q", [(t, q) for t, qs in QUESTIONS.items() for q in qs])
def test_template_sql_passes_safety_layer(template, q):
    m = ENGINE.match(q)
    assert m is not None and m.template == template, (q, m and m.template)
    safe = validate_sql(m.sql)
    assert "LIMIT" in safe.sql and {"oy", "birim", "secim"} >= set(
        t for t in ("oy", "birim", "secim") if f" {t} " in f" {m.sql} ")


def test_values_in_sql_come_from_the_lexicon():
    # the user's spelling is never pasted into SQL: 'istanbulda chp' becomes plaka 34 and 'CHP'
    m = ENGINE.match("istanbulda 2023te chp yuzde kac aldi")
    assert "b.plaka = 34" in m.sql and "'CHP'" in m.sql and "istanbulda" not in m.sql
    m = ENGINE.match("Kadikoyde 2017 referandumunda hayir orani")
    assert "'Kadıköy'" in m.sql and "'Hayır'" in m.sql


def test_party_renamed_on_the_ballot_is_explained():
    m = ENGINE.match("HDP 2023'te kaç oy aldı?")
    assert "'YEŞİL SOL'" in m.sql


def test_follow_up_merges_with_previous_question():
    hist = [Turn("2018 genel seçiminde İzmir'de birinci parti hangisiydi?")]
    m = ENGINE.match("ya 2023'te?", hist)
    assert m is not None and "s.kod = '2023'" in m.sql and "b.plaka = 35" in m.sql
    m = ENGINE.match("peki Ankara?", hist)
    assert "b.plaka = 6" in m.sql and "s.kod = '2018'" in m.sql
    m = ENGINE.match("en yüksek hangi ilde?", [Turn("2014 cumhurbaşkanlığı seçiminde Demirtaş yüzde kaç aldı?")])
    assert m.template == "en-yuksek-dusuk" and "LIMIT 1" in m.sql
    assert ENGINE.match("peki ya?", hist) is None


# ---------------------------------------------------------------------------- known answers (DB)
# Each template on questions whose verified answer is frozen in the snapshots (dev split + gold set).
KNOWN = {
    "birim-sonucu": ["b036", "b044", "b072", "b064", "b096", "b104", "g05", "g21", "g22"],
    "ulusal-oy": ["b008", "b092", "b140", "b237", "g01", "g31"],
    "kac-yerde-birinci": ["b048", "b076", "b084", "b100", "b136", "g07", "g11", "g18", "g26"],
    "en-yuksek-dusuk": ["b052", "b068", "b080", "b088", "b120", "b128", "b245", "g08", "g09", "g24", "g27", "g30"],
    "nerede-birinci": ["b040", "b060", "b132", "b144"],
    "vekil": ["b020", "b028", "b032", "g03", "g04", "g29", "g32"],
    "fark": ["b192", "b196", "b241"],
    "katilim": ["b156", "g15", "g16"],
    "secmen-sayisi": ["b152", "b204", "g23"],
    "zaman-serisi-oran": ["b160", "b164", "b168", "b172", "g12"],
    "zaman-serisi-kazanan": ["g13"],
    "oy-degisimi": ["b176", "b180", "b188"],
}


def _item(i):
    return BANK.get(i) or GOLD[i]


@pytest.mark.parametrize("template,item_id", [(t, i) for t, ids in KNOWN.items() for i in ids])
def test_template_known_answer_on_db(template, item_id):
    db = real_db_or_skip()
    it = _item(item_id)
    assert it.get("split", "dev") != "test", "known-answer tests use dev/gold items only"
    m = TemplateEngine(index=IDX).match(it["question"], [Turn(h["question"]) for h in it.get("history") or []])
    assert m is not None and m.template == template, (it["question"], m and m.template)
    res = db.run(validate_sql(m.sql).sql, 200)
    assert results_match(SNAP[item_id]["rows"], res.rows, ordered=bool(it.get("ordered"))), (m.sql, res.rows[:3])
    assert m.answer(res)                                     # a Turkish sentence is produced


def test_known_numbers_and_answer_text():
    db = real_db_or_skip()
    m = ENGINE.match("2023 genel seçiminde AK Parti Türkiye genelinde kaç oy aldı?")
    res = db.run(validate_sql(m.sql).sql, 200)
    assert res.rows[0][1] == 19127097
    text = m.answer(res)
    assert "19.127.097" in text and "%35,23" in text and "ittifak" in text      # Turkish format + caveat
    m = ENGINE.match("1963 yerel seçiminde İstanbul belediye başkanlığını kim kazandı?")
    res = db.run(validate_sql(m.sql).sql, 200)
    assert res.rows[0][0] == "CHP" and "aday" in res.columns                    # mayor names exist 1950–1989
