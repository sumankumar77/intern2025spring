#!/bin/bash
#
# Usage:
#	$ setup_postgres <appname>
#

# ###################################################################
# Generate DB password
# ###################################################################
echo "Creating secure password for database role..."
DBPASSWORD=`openssl rand -base64 32`
if [ $? -ne 0 ]; then
	    error_exit "Error creating secure password for database role."
fi
echo $DBPASSWORD > $APPFOLDERPATH/.django_db_password
chown $APPNAME:$GROUPNAME $APPFOLDERPATH/.django_db_password
