import base64
import binascii
import boto3  # type: ignore
from botocore.exceptions import ClientError  # type: ignore
from botocore.config import Config  # type: ignore
from giftless.storage import ExternalStorage  # type: ignore
from giftless.storage.exc import ObjectNotFound  # type: ignore
from giftless.util import safe_filename  # type: ignore
import posixpath
from typing import Any, Dict, Optional


class AmazonS3Storage(ExternalStorage):  # type: ignore[misc]
    def __init__(
        self,
        bucket_name: str,
        path_prefix: Optional[str] = None,
        endpoint: Optional[str] = None,
        storage_class: Optional[str] = None,
        **_: Dict[str, Any],
    ) -> None:
        config = Config(s3={"addressing_style": "virtual"})
        self._bucket_name = bucket_name
        self._path_prefix = path_prefix or ""
        self._storage_class = storage_class
        self._s3 = boto3.resource("s3", endpoint_url=endpoint)
        self._s3_client = boto3.client("s3", endpoint_url=endpoint, config=config)

    def get_upload_action(
        self,
        prefix: str,
        oid: str,
        size: int,
        expires_in: int,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        base64_oid = base64.b64encode(binascii.a2b_hex(oid)).decode("ascii")

        params = {
            "Bucket": self._bucket_name,
            "Key": self._blob_path(prefix, oid),
            "ContentType": "application/octet-stream",
            "ChecksumSHA256": base64_oid,
            "StorageClass": self._storage_class,
        }

        url = self._s3_client.generate_presigned_url(
            "put_object", Params=params, ExpiresIn=expires_in
        )

        return {
            "actions": {
                "upload": {
                    "href": url,
                    "header": {
                        "Content-Type": "application/octet-stream",
                        "X-Amz-Checksum-Sha256": base64_oid,
                    },
                    "expires_in": expires_in,
                }
            }
        }

    def get_download_action(
        self,
        prefix: str,
        oid: str,
        size: int,
        expires_in: int,
        extra: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        if extra is None:
            extra = {}

        filename = extra.get("filename")
        disposition = (
            f'attachment; filename="{safe_filename(filename)}"'
            if filename
            else extra.get("disposition", "attachment")
        )

        params = {
            "Bucket": self._bucket_name,
            "Key": self._blob_path(prefix, oid),
            "ResponseContentDisposition": disposition,
        }

        url = self._s3_client.generate_presigned_url(
            "get_object", Params=params, ExpiresIn=expires_in
        )

        return {
            "actions": {
                "download": {"href": url, "header": {}, "expires_in": expires_in}
            }
        }

    def exists(self, prefix: str, oid: str) -> bool:
        try:
            self.get_size(prefix, oid)
            return True
        except ObjectNotFound:
            return False

    def get_size(self, prefix: str, oid: str) -> int:
        try:
            obj = self._s3.Object(self._bucket_name, self._blob_path(prefix, oid))
            size = obj.content_length
            assert isinstance(size, int)
            return size
        except ClientError as e:
            raise ObjectNotFound() if e.response["Error"]["Code"] == "404" else e

    def _blob_path(self, prefix: str, oid: str) -> str:
        storage_prefix = self._path_prefix.lstrip("/")
        return posixpath.join(storage_prefix, prefix, oid)
