# Soru kalıpları (question patterns)

[`eval/soru_kaliplari.yaml`](../eval/soru_kaliplari.yaml) groups the 287 bank questions into 25 parameterised
patterns, ranked by weight (sum of the questions' frequency: yüksek 3, orta 2, düşük 1). It is the input for the
template layer in [`secim_chatbot/templates.py`](../secim_chatbot/templates.py) (see the README, "Template layer").

Each pattern has:

| Field | Meaning |
|---|---|
| `sira`, `agirlik`, `soru_sayisi`, `siklik` | rank, weight, number of bank questions, frequency breakdown |
| `kalip` | the pattern with `{slots}`, e.g. `{secim}'de {parti/aday} kaç {seviye}de birinci oldu` |
| `yuvalar` | slot → expected value type (seçim kodu, parti, il, ilçe, seviye, N) |
| `yanitlanabilir` | evet / kısmen / hayır (the `veri-yok-*` patterns should map straight to a refusal) |
| `ornekler` | up to 8 bank ids; their gold SQL is the reference implementation |
| `sql_sablonu` | SQL skeleton with `{slot}` placeholders (`...` = skeleton only; see the examples) |
| `kaynaklar` | research sources (see [RESEARCH.md](RESEARCH.md)) |

Top 5: `birim-sonucu` (result of one province/district/neighbourhood), `ulusal-oy` (national votes/share),
`kac-yerde-birinci` (how many provinces won), `en-yuksek-dusuk` (top/bottom N), `vekil` (seats).

How the template layer uses it: resolve slots first (election code with the documented defaults, party
spelling, province plate, and district *within* a province: names repeat), fill the skeleton, and send it
through the same `safety.validate_sql` path. Questions that don't fill a pattern with confidence go to the LLM
(hybrid mode) or get a "no template" reply (template mode).

Implemented: `birim-sonucu`, `ulusal-oy`, `kac-yerde-birinci`, `en-yuksek-dusuk` (incl. thresholds), `vekil`,
`referandum` (through the share / ranking / count templates with Evet/Hayır as the option), `fark` (two parties,
winner vs runner-up, closest races), `katilim`, `zaman-serisi-oran`, `nerede-birinci`, `oy-degisimi`,
`secmen-sayisi`, `zaman-serisi-kazanan`, `takip` (follow-ups merged with the previous question) and the
`veri-yok-*` patterns as rule-based refusals. Not templated (left to the LLM): `belirsiz-varsayilan` beyond the
documented election defaults, `el-degistiren`, `tur-karsilastirma`, `capraz`, `bolge-toplami`, `rekor`.

Regenerate after editing the bank: `python scripts/build_soru_kaliplari.py` (rule-based classification;
`tests/test_soru_bankasi.py` checks that ranks and example ids are consistent).
