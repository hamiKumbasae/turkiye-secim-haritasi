"""
Ham wikitext icin kucuk, bagimsiz yardimcilar: bolumlere ayirma, tablo
(wikitable / {{Secim tablosu}}) ayristirma (rowspan/colspan dahil) ve hucre
metnini duz metne indirme. Harici kutuphane gerektirmez.
"""
import re

_H = re.compile(r"^(={2,6})\s*(.*?)\s*\1\s*$", re.M)


def sections(text, level):
    """[(baslik, govde)] - verilen seviyedeki (2 -> '==x==') basliklar. Govde,
    bir sonraki AYNI ya da daha UST seviyedeki basliga kadar."""
    heads = [(m.start(), m.end(), len(m.group(1)), m.group(2)) for m in _H.finditer(text)]
    out = []
    for i, (s, e, lv, title) in enumerate(heads):
        if lv != level:
            continue
        end = len(text)
        for s2, _, lv2, _ in heads[i + 1:]:
            if lv2 <= level:
                end = s2
                break
        out.append((plain(title), text[e:end]))
    return out


def _strip_templates(s):
    # ic ice olmayan sablonlar icin yeterli; {{Yüzde|a|b|2}} gibi hucreler bos kalir
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    return s


def plain(s):
    """Hucre/baslik metnini duz metne indir."""
    s = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"\{\{\s*(?:[Kk]ısaltma|abbr)\s*\|([^|}]*)\|[^}]*\}\}", r"\1", s)
    s = re.sub(r"\{\{\s*(?:[Nn]owrap|[Ss]mall)\s*\|([^}]*)\}\}", r"\1", s)
    s = _strip_templates(s)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[https?://\S+\s*([^\]]*)\]", r"\1", s)
    s = re.sub(r"<br\s*/?>", " ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("'''", "").replace("''", "").replace("&nbsp;", " ")
    return " ".join(s.split())


def links(s):
    """Hucredeki [[hedef|metin]] linklerinin hedefleri."""
    return [m.split("|")[0].strip() for m in re.findall(r"\[\[([^\]]+)\]\]", s)]


def _split_attr(cell):
    """'style="x" | icerik' -> (attr, icerik). Link/sablon icindeki | sayilmaz."""
    depth_sq = depth_br = 0
    for i, ch in enumerate(cell):
        two = cell[i:i + 2]
        if two == "[[":
            depth_sq += 1
        elif two == "]]":
            depth_sq -= 1
        elif two == "{{":
            depth_br += 1
        elif two == "}}":
            depth_br -= 1
        elif ch == "|" and depth_sq == 0 and depth_br == 0:
            if cell[i + 1:i + 2] == "|":
                return "", cell
            return cell[:i], cell[i + 1:]
    return "", cell


def _split_inline(line, sep):
    """'a || b || c' -> ['a','b','c'] (link/sablon ici haric)."""
    parts, buf, depth_sq, depth_br, i = [], [], 0, 0, 0
    while i < len(line):
        two = line[i:i + 2]
        if two == "[[":
            depth_sq += 1
        elif two == "]]":
            depth_sq -= 1
        elif two == "{{":
            depth_br += 1
        elif two == "}}":
            depth_br -= 1
        if two == sep and depth_sq == 0 and depth_br == 0:
            parts.append("".join(buf))
            buf = []
            i += 2
            continue
        buf.append(line[i])
        i += 1
    parts.append("".join(buf))
    return parts


def _span(attr, name):
    m = re.search(name + r'\s*=\s*"?(\d+)', attr)
    return int(m.group(1)) if m else 1


def tables(text):
    """Metindeki tum tablolarin ham govdeleri. {{Seçim tablosu|...}} sablonu da
    bir tablo acar (kapanisi duz '|}')."""
    out = []
    for m in re.finditer(r"^[:\s]*(\{\||\{\{\s*Seçim tablosu[^}]*\}\})", text, re.M):
        start = m.end()
        # ic ice tablo nadir; ilk satir-basi '|}' kapanis kabul edilir
        e = re.search(r"^\s*\|\}", text[start:], re.M)
        end = start + e.start() if e else len(text)
        out.append((m.start(), text[start:end]))
    return out


def parse_table(body):
    """Tablo govdesi -> satirlar; her satir [{'raw','text','header','attr'}].
    rowspan/colspan acilir (kopya hucrelerde 'span': True)."""
    rows, cur = [], None
    pending = {}  # sutun -> [kalan, hucre]
    for line in body.split("\n"):
        ls = line.strip()
        if ls.startswith("|-"):
            if cur is not None:
                rows.append(cur)
            cur = []
            continue
        if ls.startswith("|+") or ls.startswith("{|") or not ls:
            continue
        if ls[0] in "|!":
            if cur is None:
                cur = []
            header = ls[0] == "!"
            content = ls[1:]
            parts = _split_inline(content, "!!" if header else "||")
            if header and len(parts) == 1:
                parts = _split_inline(content, "||")
            for p in parts:
                attr, c = _split_attr(p)
                cur.append({"raw": c.strip(), "text": plain(c), "header": header, "attr": attr,
                            "rowspan": _span(attr, "rowspan"), "colspan": _span(attr, "colspan")})
        elif cur:
            # onceki hucrenin devam satiri
            cur[-1]["raw"] += "\n" + line
            cur[-1]["text"] = plain(cur[-1]["raw"])
    if cur is not None:
        rows.append(cur)
    # rowspan/colspan acilimi
    grid = []
    for r in rows:
        if not r:
            continue
        out, col, it = [], 0, iter(r)
        cells = list(it)
        k = 0
        while k < len(cells) or col in pending:
            if col in pending:
                left, cell = pending[col]
                out.append(dict(cell, span=True))
                if left <= 1:
                    del pending[col]
                else:
                    pending[col] = [left - 1, cell]
                col += 1
                continue
            cell = cells[k]
            k += 1
            for c2 in range(cell["colspan"]):
                out.append(cell if c2 == 0 else dict(cell, span=True))
                if cell["rowspan"] > 1:
                    pending[col] = [cell["rowspan"] - 1, cell]
                col += 1
        grid.append(out)
    return grid


def tr_int(s):
    """'125.608' / '1,234' / '12 345' -> int; sayi degilse None."""
    s = (s or "").strip().replace(" ", " ")
    s = re.sub(r"\[.*?\]", "", s)
    if not re.fullmatch(r"[\d.,\s]+", s or "x"):
        return None
    d = re.sub(r"[.,\s]", "", s)
    return int(d) if d else None
