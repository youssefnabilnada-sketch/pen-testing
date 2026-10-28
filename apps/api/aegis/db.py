import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.engine import URL, make_url

class Base(DeclarativeBase):
    pass

def connection_url():
    """Separate components avoid interpreting punctuation in database passwords."""
    if os.getenv('DATABASE_URL'):
        return make_url(os.environ['DATABASE_URL'])
    if os.getenv('DATABASE_HOST'):
        password=os.getenv('DATABASE_PASSWORD')
        if not password:
            raise RuntimeError('DATABASE_PASSWORD is required for the configured database host.')
        return URL.create('postgresql+psycopg',username=os.getenv('DATABASE_USER','aegis'),
            password=password,host=os.environ['DATABASE_HOST'],port=int(os.getenv('DATABASE_PORT','5432')),
            database=os.getenv('DATABASE_NAME','aegis'))
    return make_url('sqlite:///./aegis.db')

url = connection_url()
options={'pool_pre_ping':True}
if url.get_backend_name()=='sqlite':
    options['connect_args']={'check_same_thread':False}
elif url.get_backend_name()=='postgresql':
    options.update(pool_size=5,max_overflow=5,pool_timeout=5,pool_recycle=1800,
                   connect_args={'connect_timeout':5,'options':'-c statement_timeout=15000'})
engine = create_engine(url, **options)
if url.get_backend_name()=='sqlite':
    @event.listens_for(engine, 'connect')
    def foreign_keys(conn, record):
        conn.execute('PRAGMA foreign_keys=ON')
Session = sessionmaker(engine, expire_on_commit=False)

def database():
    with Session() as db:
        yield db
