"""
build/mahalle_<yil>.json dosyalarini index.html'in gomulu, gzip+base64
sikistirilmis window.__EMBEDDED_GZ__ objesine ekler.

Kullanim:
  python3 gom_ve_sikistir.py <index.html yolu> <yil_anahtari>=<mahalle_json yolu> [<yil_anahtari>=<yol> ...]

Ornek:
  python3 gom_ve_sikistir.py ../../../index.html 2023cb2tur=mahalle_2023cb2tur.json 2018cb=mahalle_2018cb.json

Her <mahalle_json>, build_mahalle_aday_bazli.py veya build_mahalle_parti_bazli.py
tarafindan uretilen {geomId: [{id, ad, geometry, secmen, sandik, katilim, kazanan, oy}, ...]}
formatindaki dosyadir. Bu script:
  1. index.html'deki window.__EMBEDDED_GZ__ objesini gzip+base64'ten geri acar,
  2. mahalle_geo.json'a yeni geometrileri (osm_id bazinda tekillestirerek) ekler,
  3. mahalle_votes.json'a yeni yil(lar)in oy verisini ekler,
  4. hepsini yeniden gzip+base64'e sikistirip index.html'e geri yazar.
"""
import sys
import json
import gzip
import base64


def decompress(b64):
    return json.loads(gzip.decompress(base64.b64decode(b64)))


def compress(obj):
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(gzip.compress(raw, compresslevel=9)).decode("ascii")


def main():
    index_path = sys.argv[1]
    year_args = sys.argv[2:]
    if not year_args:
        print("En az bir <yil>=<dosya> argumani gerekli"); sys.exit(1)

    with open(index_path, encoding="utf-8") as f:
        content = f.read()

    start_marker = "window.__EMBEDDED_GZ__ = "
    start = content.find(start_marker)
    end = content.find(";\n</script>", start)
    if start == -1 or end == -1:
        print("window.__EMBEDDED_GZ__ bulunamadi - index.html henuz sikistirilmis formata gecmemis olabilir"); sys.exit(1)

    gz_obj = json.loads(content[start + len(start_marker):end])
    geo = decompress(gz_obj["mahalle_geo.json"])
    votes = decompress(gz_obj["mahalle_votes.json"])
    print("mevcut geo ilce sayisi:", len(geo))
    print("mevcut yillar:", list(votes.keys()))

    for arg in year_args:
        year_key, path = arg.split("=", 1)
        data = json.load(open(path, encoding="utf-8"))
        votes[year_key] = {}
        for geom_id, rows in data.items():
            geo.setdefault(geom_id, {})
            vote_rows = {}
            for r in rows:
                osm_id = r["id"]
                if osm_id not in geo[geom_id]:
                    geo[geom_id][osm_id] = {"ad": r["ad"], "geometry": r["geometry"]}
                vote_rows[osm_id] = {
                    "secmen": r["secmen"], "sandik": r["sandik"], "katilim": r["katilim"],
                    "kazanan": r["kazanan"], "oy": r["oy"],
                }
            votes[year_key][geom_id] = vote_rows
        print(f"  + {year_key}: {len(votes[year_key])} ilce eklendi")

    gz_obj["mahalle_geo.json"] = compress(geo)
    gz_obj["mahalle_votes.json"] = compress(votes)

    new_obj_str = json.dumps(gz_obj, ensure_ascii=False, separators=(",", ":"))
    new_content = content[:start + len(start_marker)] + new_obj_str + content[end:]
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("yeni index.html boyutu:", len(new_content), "bayt")


if __name__ == "__main__":
    main()
