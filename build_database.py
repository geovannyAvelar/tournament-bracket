import os
from config import db

if os.path.exists('tournament.db'):
    os.remove('tournament.db')

db.create_all()
db.session.commit()