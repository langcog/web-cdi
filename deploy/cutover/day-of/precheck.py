from django.db import connection
c = connection.cursor()
c.execute('select count(*) from (select instrument_id, title from "researcher_UI_instrumentscore" group by 1,2 having count(*)>1) d')
print("CHECK duplicate score titles (must be 0):", c.fetchone()[0])
c.execute("select domain from django_site where id=1")
print("CHECK site 1 (expect www.webcdi.org):", c.fetchone()[0])
c.execute("select count(*) from django_migrations")
print("CHECK applied migrations:", c.fetchone()[0])
