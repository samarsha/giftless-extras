#!/usr/bin/env python3

import argparse
import json
from typing import Any, Dict, List, Union
import jwt
import sys
import time
from urllib.parse import urljoin
from pathlib import Path

KEY_FILE = "jwt-rs256.key"
ENDPOINT = "https://lfs.example.com/"
SCOPES = ["obj:my-org/my-repo.git"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("operation", choices=["download", "upload"])
    args = parser.parse_args()
    key = Path(KEY_FILE).read_text()
    token = authenticate(key, ENDPOINT, SCOPES, args.path)
    json.dump(token, sys.stdout)


def authenticate(
    key: str, endpoint: str, scopes: List[str], path: str
) -> Dict[str, Any]:
    expires_in = 3600
    exp = int(time.time()) + expires_in
    payload = {"exp": exp, "scopes": scopes}
    token = to_ascii(jwt.encode(payload, key, "RS256"))
    return {
        "href": urljoin(endpoint, path.lstrip("/")),
        "header": {"Authorization": f"Bearer {token}"},
        "expires_in": expires_in,
    }


def to_ascii(s: Union[bytes, str]) -> str:
    return s.decode("ascii") if isinstance(s, bytes) else s


if __name__ == "__main__":
    main()
