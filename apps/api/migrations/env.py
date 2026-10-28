from alembic import context
from sqlalchemy import engine_from_config, pool
from aegis.db import Base, connection_url
from aegis import models  # noqa: F401
config=context.config
config.set_main_option('sqlalchemy.url',connection_url().render_as_string(hide_password=False).replace('%','%%'))
if context.is_offline_mode():
    context.configure(url=config.get_main_option('sqlalchemy.url'),target_metadata=Base.metadata,literal_binds=True)
    with context.begin_transaction():context.run_migrations()
else:
    engine=engine_from_config(config.get_section(config.config_ini_section),prefix='sqlalchemy.',poolclass=pool.NullPool)
    with engine.begin() as connection:
        context.configure(connection=connection,target_metadata=Base.metadata,compare_type=True)
        with context.begin_transaction():context.run_migrations()
