"""Management commands.  Usage: python -m app.cli create-admin --username NAME --email ADDR"""
import argparse
import getpass
import sys

from pydantic import ValidationError

from app.db.database import get_sessionmaker
from app.schemas.user import UserCreate
from app.services.users import UserExists, create_user


def create_admin(username: str, email: str) -> int:
    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Confirm password: "):
        print("Passwords do not match.", file=sys.stderr)
        return 1
    try:
        data = UserCreate(username=username, email=email, password=password, is_admin=True)
    except ValidationError as exc:
        for e in exc.errors():
            print(f"Error: {e['msg'].removeprefix('Value error, ')}", file=sys.stderr)
        return 1
    with get_sessionmaker()() as db:
        try:
            create_user(db, data)
        except UserExists:
            print("Error: username or email already exists.", file=sys.stderr)
            return 1
    print(f"Admin '{data.username}' created.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("create-admin", help="Create an administrator account")
    p.add_argument("--username", required=True)
    p.add_argument("--email", required=True)
    args = parser.parse_args()
    return create_admin(args.username, args.email)


if __name__ == "__main__":
    raise SystemExit(main())
