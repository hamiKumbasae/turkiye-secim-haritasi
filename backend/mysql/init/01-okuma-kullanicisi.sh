#!/bin/bash
# MySQL ilk kurulumunda bir kez çalışır: election-api için yalnız SELECT yetkili kullanıcı.
set -euo pipefail
mysql --protocol=socket -uroot -p"${MYSQL_ROOT_PASSWORD}" <<SQL
CREATE USER IF NOT EXISTS '${DB_READ_USER}'@'%' IDENTIFIED BY '${DB_READ_PASSWORD}';
GRANT SELECT ON \`${MYSQL_DATABASE}\`.* TO '${DB_READ_USER}'@'%';
FLUSH PRIVILEGES;
SQL
