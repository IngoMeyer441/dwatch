import os
from configparser import ConfigParser
from enum import Enum, auto
from typing import Any, Dict, List, Optional, TextIO, Union

from .mail import MailBackend, MailEncryption
from .monitor import CaptureStream, UnknownCaptureStreamError

CONFIG_FILEPATH = "~/.dwatchrc"


class UnknownMailBackendError(Exception):
    pass


class UnknownMailEncryptionError(Exception):
    pass


class UnknownVerbosityLevelError(Exception):
    pass


class Verbosity(Enum):
    QUIET = auto()
    ERROR = auto()
    WARN = auto()
    VERBOSE = auto()
    DEBUG = auto()


class Config:
    _default_config: Dict[str, Dict[str, Any]] = {
        "general": {
            "wait_for_lock": True,
            "verbosity": "verbose",
        },
        "mail": {
            "backend": "sendmail",
            "server": "mail.example.com",
            "login_user": "jane.doe",
            "login_password": "xxx",
            "encryption": "starttls",
            "from_address": "dwatch-report@example.com",
            "to_addresses": "admin@example.com",
        },
        "watch": {
            "abort_on_error": False,
            "capture": "stdout,stderr",
            "ignore_output_on_error": False,
            "interval": 60.0,
            "run_once": False,
            "shell": False,
        },
    }

    @classmethod
    def write_default_config(cls, config_filepath_or_file: Union[str, TextIO] = CONFIG_FILEPATH) -> None:
        default_config = ConfigParser(allow_no_value=True)
        default_config.read_dict(cls._default_config)
        if isinstance(config_filepath_or_file, str):
            config_directory_path = os.path.dirname(os.path.expanduser(config_filepath_or_file))
            if not os.path.exists(config_directory_path):
                os.makedirs(config_directory_path)
            config_file: TextIO
            with open(
                os.path.expanduser(config_filepath_or_file),
                "w",
                encoding="utf-8",
                opener=lambda path, flags: os.open(path, flags, 0o600),
            ) as config_file:
                default_config.write(config_file)
        else:
            config_file = config_filepath_or_file
            default_config.write(config_file)

    def __init__(
        self,
        config_filepath: Optional[str] = CONFIG_FILEPATH,
    ) -> None:
        self._config_filepath = os.path.expanduser(config_filepath) if config_filepath is not None else None
        self._config = ConfigParser(allow_no_value=True)
        self._config.read_dict(self._default_config)
        self.read_config()

    def read_config(self, config_filepath: Optional[str] = None) -> None:
        if config_filepath is not None:
            self._config_filepath = config_filepath
        if self._config_filepath is not None:
            self._config.read(self._config_filepath)

    @property
    def config_filepath(self) -> str:
        assert self._config_filepath is not None
        return self._config_filepath

    @property
    def mail_backend(self) -> MailBackend:
        backend_string = self._config["mail"]["backend"]
        if backend_string.upper() not in MailBackend.__dict__:
            raise UnknownMailBackendError(
                f'The mail backend "{backend_string}" is unknown. You can choose from "sendmail" or "smtplib".'
            )
        return MailBackend[backend_string.upper()]

    @property
    def mail_encryption(self) -> MailEncryption:
        encryption_string = self._config["mail"]["encryption"]
        if encryption_string.upper() not in MailEncryption.__dict__:
            raise UnknownMailEncryptionError(
                f'The mail encryption "{encryption_string}" is unknown.'
                ' You can choose from "none", "starttls" or "ssl".'
            )
        return MailEncryption[encryption_string.upper()]

    @property
    def mail_from_address(self) -> str:
        return self._config["mail"]["from_address"]

    @property
    def mail_to_addresses(self) -> List[str]:
        return [address.strip() for address in self._config["mail"]["to_addresses"].split(",")]

    @property
    def mail_login_password(self) -> str:
        return self._config["mail"]["login_password"]

    @property
    def mail_login_user(self) -> str:
        return self._config["mail"]["login_user"]

    @property
    def mail_server(self) -> str:
        return self._config["mail"]["server"]

    @property
    def verbosity(self) -> Verbosity:
        verbosity_string = self._config["general"]["verbosity"]
        if verbosity_string.upper() not in Verbosity.__dict__:
            raise UnknownVerbosityLevelError(
                f'The verbosity level "{verbosity_string}" is unknown.'
                ' You can choose from "quiet", "error", "warn", "verbose" or "debug".'
            )
        return Verbosity[verbosity_string.upper()]

    @property
    def abort_on_error(self) -> bool:
        return self._config["watch"].getboolean(
            "abort_on_error", fallback=self._default_config["watch"]["abort_on_error"]
        )

    @property
    def capture(self) -> CaptureStream:
        capture_string_list = self._config["watch"]["capture"]
        capture = CaptureStream(0)
        for capture_string in capture_string_list.split(","):
            if capture_string.upper() not in CaptureStream.__dict__:
                raise UnknownCaptureStreamError(
                    f'The capture stream "{capture_string}" is unknown.'
                    ' You can choose from "stdout" or "stderr" or combine them with ",".'
                )
            capture |= CaptureStream[capture_string.upper()]
        return capture

    @property
    def ignore_output_on_error(self) -> bool:
        return self._config["watch"].getboolean(
            "ignore_output_on_error", fallback=self._default_config["watch"]["ignore_output_on_error"]
        )

    @property
    def interval(self) -> float:
        return self._config["watch"].getfloat("interval", fallback=self._default_config["watch"]["interval"])

    @property
    def run_once(self) -> bool:
        return self._config["watch"].getboolean("run_once", fallback=self._default_config["watch"]["run_once"])

    @property
    def shell(self) -> bool:
        return self._config["watch"].getboolean("shell", fallback=self._default_config["watch"]["shell"])

    @property
    def wait_for_lock(self) -> bool:
        return self._config["general"].getboolean(
            "wait_for_lock", fallback=self._default_config["general"]["wait_for_lock"]
        )


config = Config()
