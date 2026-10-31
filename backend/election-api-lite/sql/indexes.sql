-- Optional, additive indexes for election-api. They do not change any table or data and are safe to
-- apply while other programs read the database. scripts/db_yukle.py drops and recreates the tables,
-- so re-apply this file after every reload.
--
--   mariadb -h 192.168.1.2 -u hami -p secim < backend/election-api/sql/indexes.sql
--
-- Measured on the full dataset (640k birim, 2.8M oy rows), MariaDB 10.11:
--   party history for a province/district   ~0.1 s  -> ~0.01 s   (ix_birim_seviye_plaka_ad)
--   name search (contains, grouped)         ~0.8 s  -> ~0.4 s    (ix_birim_ad_cover, index-only scan)
-- Both use CREATE INDEX IF NOT EXISTS, so running the file twice is harmless.

-- /api/v1/history: units of one level in one province (or one district of it by name) across all elections.
-- The existing (secim_id, seviye, plaka) index cannot serve it because secim_id is not fixed.
CREATE INDEX IF NOT EXISTS ix_birim_seviye_plaka_ad ON birim (seviye, plaka, ad);

-- /api/v1/search: LIKE '%text%' cannot seek, but scanning this narrow covering index is much cheaper
-- than scanning the whole table (no row lookups, GROUP BY columns are all in the index).
CREATE INDEX IF NOT EXISTS ix_birim_ad_cover ON birim (ad, seviye, geom_id, ust_geom_id, secim_id, plaka);
