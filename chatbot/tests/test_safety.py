import pytest

from secim_chatbot.safety import UnsafeSQLError, validate_sql

ALLOWED = [
    "SELECT ad FROM birim WHERE plaka = 34",
    "select o.aday_parti, sum(o.oy) from oy o join birim b on b.id = o.birim_id group by 1",
    "WITH t AS (SELECT * FROM oy) SELECT birim_id FROM t",
    "SELECT kod FROM secim UNION SELECT ad FROM birim",
    "SELECT ad FROM secim.birim",
    "SELECT ad FROM birim WHERE ad LIKE '%ş%' AND ad = 'İstanbul'",
    "SELECT COUNT(*) FROM birim b WHERE EXISTS (SELECT 1 FROM oy o WHERE o.birim_id = b.id)",
    "SELECT ROUND(100 * SUM(CASE WHEN aday_parti = 'Evet' THEN oy ELSE 0 END) / SUM(oy), 2) FROM oy",
    "```sql\nSELECT ad FROM birim;\n```",
    "SELECT ad FROM birim;",
]

REJECTED = [
    ("", "Boş"),
    ("SELECT 1; DROP TABLE oy", "Tek bir"),
    ("SELECT ad FROM birim; SELECT 1", "Tek bir"),
    ("DELETE FROM oy", "SELECT"),
    ("UPDATE birim SET ad = 'x'", "SELECT"),
    ("INSERT INTO secim (kod) VALUES ('x')", "SELECT"),
    ("DROP TABLE oy", "SELECT"),
    ("CREATE TABLE x (a int)", "SELECT"),
    ("TRUNCATE TABLE oy", None),
    ("SET @a = 1", None),
    ("SHOW TABLES", None),
    ("GRANT ALL ON *.* TO 'x'", None),
    ("SELECT * FROM mahalle", "tablo"),
    ("SELECT * FROM ek_veri", "tablo"),
    ("SELECT * FROM information_schema.tables", "şema"),
    ("SELECT * FROM mysql.user", "şema"),
    ("SELECT * FROM (SELECT * FROM user) x", "tablo"),
    ("SELECT SLEEP(10)", "SLEEP"),
    ("SELECT BENCHMARK(100000000, MD5('a'))", "BENCHMARK"),
    ("SELECT LOAD_FILE('/etc/passwd')", "LOAD_FILE"),
    ("SELECT VERSION()", None),
    ("SELECT USER()", None),
    ("SELECT CURRENT_USER()", None),
    ("SELECT DATABASE()", None),
    ("SELECT @@version", None),
    ("SELECT ad FROM birim INTO OUTFILE '/tmp/x'", None),
    ("SELECT ad FROM birim FOR UPDATE", "FOR UPDATE"),
    ("SELECT ad FROM birim WHERE", None),
    ("hangi parti kazandı?", None),
]


@pytest.mark.parametrize("sql", ALLOWED)
def test_allowed(sql):
    safe = validate_sql(sql)
    assert safe.sql.upper().lstrip().startswith(("SELECT", "WITH"))


@pytest.mark.parametrize("sql,fragment", REJECTED)
def test_rejected(sql, fragment):
    with pytest.raises(UnsafeSQLError) as e:
        validate_sql(sql)
    if fragment:
        assert fragment.lower() in str(e.value).lower()


def test_limit_added_when_missing():
    safe = validate_sql("SELECT ad FROM birim", max_rows=50)
    assert safe.limit_added and safe.limit == 50
    assert "LIMIT 50" in safe.sql


def test_limit_kept_when_small():
    safe = validate_sql("SELECT ad FROM birim LIMIT 5", max_rows=50)
    assert not safe.limit_added and safe.limit == 5
    assert "LIMIT 5" in safe.sql


def test_limit_clamped_when_too_large():
    safe = validate_sql("SELECT ad FROM birim LIMIT 100000", max_rows=50)
    assert safe.limit_added and "LIMIT 50" in safe.sql and "100000" not in safe.sql


def test_offset_preserved():
    safe = validate_sql("SELECT ad FROM birim LIMIT 10 OFFSET 20", max_rows=50)
    assert "LIMIT 10" in safe.sql and "OFFSET 20" in safe.sql


def test_union_gets_outer_limit():
    safe = validate_sql("SELECT kod FROM secim UNION SELECT ad FROM birim", max_rows=7)
    assert safe.sql.rstrip().endswith("LIMIT 7")


def test_comments_are_stripped():
    safe = validate_sql("SELECT ad /* gizli */ FROM birim -- yorum")
    assert "gizli" not in safe.sql and "yorum" not in safe.sql


def test_cte_name_shadowing_forbidden_table_is_checked():
    # a CTE named like an allowed table must not hide a forbidden source inside it
    with pytest.raises(UnsafeSQLError):
        validate_sql("WITH oy AS (SELECT * FROM mysql.user) SELECT * FROM oy")


def test_turkish_literals_survive_regeneration():
    safe = validate_sql("SELECT ad FROM birim WHERE ad = 'Kadıköy' AND kazanan = 'İYİ Parti'")
    assert "'Kadıköy'" in safe.sql and "'İYİ Parti'" in safe.sql
