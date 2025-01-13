#!/bin/bash
#
# Usage:
#	$ reset_migration.sh
#
APPUSER='chealth'
DBNAME='chealth'
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "This will delete the database and all migration files."
while true; do
  read -p "Do you want to continue (Y/n)" yn
  case $yn in
    [Y] ) 
      find ../apps/*/migrations/ -name "*.py" -not -name "__init__.py" -delete
      find ../apps/*/migrations/ -name "*.pyc" -delete
      sudo -u postgres psql -c "DROP DATABASE $DBNAME;"
      sudo -u postgres psql -c "CREATE DATABASE $DBNAME OWNER $APPUSER;"
      python ../manage.py makemigrations
      python ../manage.py migrate
      exit
      ;;
    *)
      exit
  esac
done

