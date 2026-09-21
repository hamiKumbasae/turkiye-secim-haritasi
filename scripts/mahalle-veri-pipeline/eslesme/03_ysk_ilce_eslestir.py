import json
import unicodedata

def fold(s):
    if s is None:
        return ""
    s = s.strip()
    s = s.replace("İ", "I").replace("ı", "i").replace("Ğ", "G").replace("ğ", "g")
    s = s.replace("Ü", "U").replace("ü", "u").replace("Ş", "S").replace("ş", "s")
    s = s.replace("Ö", "O").replace("ö", "o").replace("Ç", "C").replace("ç", "c")
    s = s.upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace(".", "").replace("-", " ").replace("'", "")
    s = " ".join(s.split())
    return s

OUT = "/private/tmp/claude-501/-Users-hamikumbasar-Desktop-Turkiye-Secim-Haritasi/09ece001-ee3a-4169-9c6c-01e7aec72612/scratchpad/osm_mahalle"

# project's authoritative ilce list (plaka, ad, geomId) from the CB 2023 2nd tur bundle
proj = json.load(open("/Users/hamikumbasar/Desktop/2023_Secim_Verileri/1950_2023_tam_veri_seti.json", encoding="utf-8"))
proj_ilceler = proj["secimler"]["2023cb2tur"]["ilceler"]
proj_index = {}
for row in proj_ilceler:
    key = (row["plaka"], fold(row["ad"]))
    proj_index[key] = row["geomId"]
print("project ilce count:", len(proj_ilceler), "unique keys:", len(proj_index))

# YSK numeric ilce list
ysk = json.load(open(f"{OUT}/ysk_ilceler.json", encoding="utf-8"))
print("YSK ilce count:", len(ysk))

matched = []
unmatched = []
for row in ysk:
    ilce_norm = fold(row["ilce_ADI"])
    il_norm = fold(row["il_ADI"])
    key = (row["il_ID"], ilce_norm)
    geomId = proj_index.get(key)
    if not geomId and ilce_norm == (il_norm + " MERKEZ"):
        geomId = proj_index.get((row["il_ID"], "MERKEZ"))
    if geomId:
        matched.append({**row, "geomId": geomId})
    else:
        unmatched.append(row)

print("matched:", len(matched), "unmatched:", len(unmatched))
print("--- sample unmatched (first 30) ---")
for u in unmatched[:30]:
    print(u["il_ID"], u["il_ADI"], "/", u["ilce_ADI"])

json.dump(matched, open(f"{OUT}/ysk_ilce_matched.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(unmatched, open(f"{OUT}/ysk_ilce_unmatched.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
