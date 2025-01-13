#!/bin/bash
#
# Usage:
#	$ install.sh <appname>
#

# Update apg-get
echo "Updating apt-get ..."
apt-get update
apt-get -y upgrade

# PostgreSQL
echo "Installing the dependencies to use PostgreSQL with Python/Django..."
apt-get -y install build-essential libpq-dev python-dev
echo "Installing the PostgreSQL Server..."
apt-get -y install postgresql postgresql-contrib

# Nginx
echo "Installing Nginx..."
apt-get -y install nginx

# Supervisor
echo "Installing Supervisor..."
apt-get -y install supervisor
echo "Enable and start the Supervisor..."
systemctl enable supervisor
systemctl start supervisor

# Python Virtualenv
echo "Installing pyenv..."
apt-get -y install make build-essential libssl-dev zlib1g-dev libbz2-dev \
	libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev \
	libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev \
	python-openssl git
git clone https://github.com/pyenv/pyenv.git ~/.pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n eval "$(pyenv init -)"\nfi' >> ~/.bashrc
source ~/.bashrc

# Configure PostgreSQL
echo "Creating PostgreSQL role '$APPNAME'..."
su postgres -c "createuser -S -D -R -w $APPNAME"
echo "Changing pasword of database role..."
su postgres -c "psql -c \"ALTER USER $APPNAME WITH PASSWORD '$DBPASSWORD';\""
echo "Creating PostgreSQL database '$APPNAME'..."
su postgres -c "createdb --owner $APPNAME $APPNAME"


# Configure Python virtualenv
echo "Configuring Python virtualenv..."
pyenv install 3.10.0


