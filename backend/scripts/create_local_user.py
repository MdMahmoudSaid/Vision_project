"""Create or update a local admin/guard account for manual testing and first-run setup.

There is no POST /auth/register endpoint by design (see contracts/local-api.yaml
and the constitution's local Admin/Guard account scope) - accounts are
provisioned locally, not over the network. Usage:

    python scripts/create_local_user.py --username admin1 --password changeme123 --role admin
"""

import argparse
import sys

from local_attendance.auth.password import hash_password
from local_attendance.database import SessionLocal
from local_attendance.models.user import LocalUser, UserRole


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--role", choices=[role.value for role in UserRole], required=True)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = db.query(LocalUser).filter_by(username=args.username).first()
        if user is None:
            user = LocalUser(
                username=args.username,
                password_hash=hash_password(args.password),
                role=UserRole(args.role),
                active=True,
            )
            db.add(user)
            action = "Created"
        else:
            user.password_hash = hash_password(args.password)
            user.role = UserRole(args.role)
            user.active = True
            action = "Updated"
        db.commit()
        print(f"{action} local user '{args.username}' with role '{args.role}'.")
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
