"""FTP synchronization using pyftpsync."""

from pathlib import Path

from ftpsync.ftp_target import FTPTarget
from ftpsync.synchronizers import UploadSynchronizer
from ftpsync.targets import FsTarget

from quantify.config.settings import FtpSyncSettings


class FtpSyncer:
    """Handles FTP upload of exported files."""

    def __init__(self, settings: FtpSyncSettings) -> None:
        """Initialize FTP syncer with settings.

        Args:
            settings: FTP synchronization settings.
        """
        self._settings = settings

    def sync(self, local_path: Path) -> None:
        """Upload local directory to FTP server.

        Args:
            local_path: Local directory to upload.
        """
        local = FsTarget(str(local_path))

        ftp_url = (
            f"ftp://{self._settings.username}:{self._settings.password}"
            f"@{self._settings.host}:{self._settings.port}{self._settings.remote_path}"
        )

        remote = FTPTarget(
            ftp_url,
            timeout=self._settings.timeout,
        )

        opts = {
            "resolve": "local",  # Local files win (overwrite remote)
            "delete": False,  # Don't delete remote files not in local
        }

        syncer = UploadSynchronizer(local, remote, opts)
        syncer.run()
