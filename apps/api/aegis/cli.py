"""Explicit local administrator setup; no default passwords or public elevation route."""
import argparse
from sqlalchemy import select
from .db import Session
from .models import User
parser=argparse.ArgumentParser()
parser.add_argument('command',choices=['promote-admin'])
parser.add_argument('email')
a=parser.parse_args()
with Session() as db:
    u=db.scalar(select(User).where(User.email==a.email.lower(),User.verified.is_(True)))
    if not u:raise SystemExit('Register and verify this account first.')
    u.superadmin=True
    db.commit()
    print('Platform administrator role granted to the specified verified account.')
