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

        remote = FTPTarget(
            path=self._settings.remote_path,
            host=self._settings.host,
            port=self._settings.port,
            username=self._settings.username,
            password=self._settings.password,
            timeout=self._settings.timeout,
            extra_opts={"create_folder": True},
        )

        opts = {
            "resolve": "local",  # Local files win (overwrite remote)
            "delete": False,  # Don't delete remote files not in local
        }

        syncer = UploadSynchronizer(local, remote, opts)
        syncer.run()
