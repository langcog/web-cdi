cd ~/web-cdi/
git pull origin master
source .env/bin/activate
cd webcdi
pip install -r requirements.txt
python manage.py collectstatic
python manage.py makemigrations
python manage.py migrate
