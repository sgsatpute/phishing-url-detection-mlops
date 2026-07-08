import shutil
import subprocess


class S3SyncError(RuntimeError):
    """Raised when an `aws s3 sync` command fails or the AWS CLI is missing."""


class S3Sync:
    def _run_sync(self, args: list[str]) -> None:
        if shutil.which("aws") is None:
            raise S3SyncError(
                "AWS CLI not found on PATH. Install it (or add it to the "
                "container image) to enable S3 sync.",
            )
        # os.system() previously swallowed the exit code entirely, so a
        # missing AWS CLI or bad/expired credentials failed *silently* —
        # the pipeline would report success even though nothing was synced.
        # subprocess.run(..., check=True) surfaces that failure instead.
        result = subprocess.run(args, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise S3SyncError(
                f"`{' '.join(args)}` failed (exit {result.returncode}): {result.stderr.strip()}",
            )

    def sync_folder_to_s3(self, folder: str, aws_bucket_url: str) -> None:
        self._run_sync(["aws", "s3", "sync", str(folder), aws_bucket_url])

    def sync_folder_from_s3(self, folder: str, aws_bucket_url: str) -> None:
        self._run_sync(["aws", "s3", "sync", aws_bucket_url, str(folder)])
