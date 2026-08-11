import getpass
import hashlib
import secrets


PBKDF2_ITERATIONS = 310_000


def main():
    password = getpass.getpass("Enter password: ")
    confirm = getpass.getpass("Confirm password: ")

    if not password:
        raise SystemExit("Password cannot be blank.")

    if password != confirm:
        raise SystemExit("Passwords do not match.")

    salt = secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()

    print("\nCopy this value into Streamlit Secrets:\n")
    print(
        f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"
    )


if __name__ == "__main__":
    main()
