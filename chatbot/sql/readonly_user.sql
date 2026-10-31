-- Read-only database user for the election chatbot.
--
-- The chatbot never needs to write. Giving it its own user with SELECT only means that
-- even a bug in the SQL safety layer cannot change data. Run once as an admin user:
--
--   mysql -h 192.168.1.2 -u root -p < chatbot/sql/readonly_user.sql
--
-- Change the password before running (and put the same value in DB_PASSWORD).
-- '%' allows connections from the LAN (e.g. the Mac); restrict it to '192.168.1.%' if you prefer.

CREATE USER IF NOT EXISTS 'secim_okur'@'%' IDENTIFIED BY 'degistir-beni';
CREATE USER IF NOT EXISTS 'secim_okur'@'localhost' IDENTIFIED BY 'degistir-beni';

-- Only the three tables the chatbot is allowed to query (mahalle geometries and ek_veri are not needed).
GRANT SELECT ON secim.secim TO 'secim_okur'@'%', 'secim_okur'@'localhost';
GRANT SELECT ON secim.birim TO 'secim_okur'@'%', 'secim_okur'@'localhost';
GRANT SELECT ON secim.oy    TO 'secim_okur'@'%', 'secim_okur'@'localhost';

-- Defence in depth: cap resources per user (MariaDB syntax).
ALTER USER 'secim_okur'@'%'         WITH MAX_USER_CONNECTIONS 10 MAX_STATEMENT_TIME 15;
ALTER USER 'secim_okur'@'localhost' WITH MAX_USER_CONNECTIONS 10 MAX_STATEMENT_TIME 15;

FLUSH PRIVILEGES;
