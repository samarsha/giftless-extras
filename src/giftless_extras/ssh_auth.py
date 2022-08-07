import argparse
import json
import jwt
import sys
import time
from urllib.parse import urljoin


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--scope", nargs="+", required=True)
    parser.add_argument("--path", required=True)
    args = parser.parse_args()

    expires_in = 3600
    exp = int(time.time()) + expires_in
    payload = {"exp": exp, "scopes": args.scope}
    token = jwt.encode(payload, args.key, "RS256").decode("ascii")

    auth = {
        "href": urljoin(args.endpoint, args.path.lstrip("/")),
        "header": {"Authorization": f"Bearer {token}"},
        "expires_in": expires_in,
    }

    json.dump(auth, sys.stdout)


if __name__ == "__main__":
    run()
