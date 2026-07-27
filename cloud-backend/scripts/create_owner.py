import argparse
import sys

from sqlalchemy import select

from cloud_attendance.auth.password import hash_password
from cloud_attendance.database import SessionLocal
from cloud_attendance.models.cloud_user import CloudRole, CloudUser


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the initial owner account")
    parser.add_argument("email", type=str, help="Owner email address")
    parser.add_argument("password", type=str, help="Owner password")
    args = parser.parse_args()

    with SessionLocal() as db:
        existing = db.scalar(select(CloudUser).where(CloudUser.email == args.email))
        if existing:
            print(f"Error: User {args.email} already exists.", file=sys.stderr)
            sys.exit(1)

        user = CloudUser(
            email=args.email,
            password_hash=hash_password(args.password),
            role=CloudRole.owner,
            active=True,
        )
        db.add(user)
        db.commit()

        print(f"Success: Owner account {args.email} created.")


if __name__ == "__main__":
    main()
