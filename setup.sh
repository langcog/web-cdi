#Execute these commands in order to load the git repo
#sudo apt-get install git 
#git clone https://github.com/langcog/web-cdi.git
#cd web-cdi

#sudo apt-get python-pip python-dev postgresql-client postgresql postgresql-contrib pgadmin5 python-psycopg2 libpq-dev libxml2-dev libxslt-dev supervisor nginx
#sudo pip install virtualenv
#virtualenv .env
#source .env/bin/activate
cd webcdi
#pip install -r requirements.txt

#Server setup
#pip install gunicorn
#sudo cp ~/webcdi.conf /etc/supervisor/conf.d/
#sudo supervisorctl reread
#sudo supervisorctl update
#refer to https://www.digitalocean.com/community/tutorials/how-to-install-and-manage-supervisor-on-ubuntu-and-debian-vps

#sudo cp ~/web-cdi-nginx.conf /etc/nginx/conf.d/
#sudo -u postgres createdb webcdi-admin
#sudo -u postgres createuser -P -s webcdi-admin
#sudo -u postgres psql -c 'GRANT ALL PRIVILEGES ON DATABASE "webcdi-admin" TO "webcdi-admin";'
#python manage.py createsuperuser
python manage.py makemigrations
python manage.py migrate

#manually add the instruments. It can be automated but then it overwrites all of the data. So it is risky in case it gets automatically executed. To add the instruments go to /admin/ and click on Add button for Instruments model.

sudo -u postgres psql -d webcdi-admin -c "\\COPY cdi_forms_english_wg FROM 'cdi_form_csv/[English_WG].csv' WITH (FORMAT csv, HEADER True)"
