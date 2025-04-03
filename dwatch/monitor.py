import datetime
import json
import logging
import os
import signal
import zlib
from base64 import b64decode, b64encode
from enum import Flag, auto
from subprocess import run
from time import sleep
from types import FrameType
from typing import Generator, NamedTuple, Optional, Sequence, Tuple

DEFAULT_INTERVAL = 60.0  # seconds
ORIGINAL_COMMAND_OUTPUT_FILEPATH = os.path.expanduser("~/.dwatch_command_output.json")


logger = logging.getLogger(__name__)


class UnknownCaptureStreamError(Exception):
    pass


class Interrupt(Exception):
    pass


class CaptureStream(Flag):
    STDOUT = auto()
    STDERR = auto()

    @classmethod
    def from_text(cls, text: str) -> "CaptureStream":
        flag = cls(0)
        for text_flag in text.split(","):
            try:
                flag |= cls[text_flag.upper()]
            except KeyError as e:
                raise UnknownCaptureStreamError(
                    'The capture stream "{}" is unknown.'.format(text_flag)
                    + ' You can choose from "stdout" or "stderr" or combine them with ",".'
                ) from e
        return flag

    @property
    def text(self) -> str:
        return ",".join(str(flag.name).lower() for flag in self)


class CommandOutput(NamedTuple):
    output: str
    timestamp: str


def watch(
    command: Sequence[str],
    shell: bool = False,
    once: bool = True,
    interval: float = DEFAULT_INTERVAL,
    capture: CaptureStream = CaptureStream.STDOUT | CaptureStream.STDERR,
    ignore_output_on_error: bool = False,
    abort_on_error: bool = False,
) -> Generator[Tuple[CommandOutput, CommandOutput], None, None]:
    def get_original_output() -> Optional[CommandOutput]:
        original_output: Optional[CommandOutput] = None
        try:
            with open(ORIGINAL_COMMAND_OUTPUT_FILEPATH, "r", encoding="utf-8") as f:
                command_output_dict = json.load(f)[b64encode(" ".join(command).encode("utf-8")).decode("utf-8")]
                original_output = CommandOutput(
                    zlib.decompress(b64decode(command_output_dict["output"].encode("utf-8"))).decode("utf-8"),
                    command_output_dict["timestamp"],
                )
        except (KeyError, OSError):
            pass
        return original_output

    def save_command_output(command_output: CommandOutput) -> None:
        command_db = {}
        try:
            with open(ORIGINAL_COMMAND_OUTPUT_FILEPATH, "r", encoding="utf-8") as f:
                command_db = json.load(f)
        except OSError:
            pass
        command_db[b64encode(" ".join(command).encode("utf-8")).decode("utf-8")] = {
            "output": b64encode(zlib.compress(command_output.output.encode("utf-8"))).decode("utf-8"),
            "timestamp": command_output.timestamp,
        }
        with open(
            ORIGINAL_COMMAND_OUTPUT_FILEPATH,
            "w",
            encoding="utf-8",
            opener=lambda path, flags: os.open(path, flags, 0o600),
        ) as f:
            json.dump(command_db, f)

    def interrupt_handler(sig: int, frame: Optional[FrameType]) -> None:
        raise Interrupt("Process was interrupted by {}.".format(signal.Signals(sig).name))

    original_sigint_handler = signal.signal(signal.SIGINT, interrupt_handler)
    original_sigterm_handler = signal.signal(signal.SIGTERM, interrupt_handler)
    original_output = None
    try:
        original_output = get_original_output()
        while True:
            command_result = run(
                command,
                capture_output=True,
                check=abort_on_error,
                shell=shell,
                text=True,
            )
            logger.debug("Command return code: %s", command_result.returncode)
            logger.debug("Command stdout: %s", command_result.stdout)
            logger.debug("Command stderr: %s", command_result.stderr)
            if command_result.returncode == 0 or not ignore_output_on_error:
                current_output = CommandOutput(
                    (
                        command_result.stdout + command_result.stderr
                        if CaptureStream.STDOUT in capture and CaptureStream.STDERR in capture
                        else command_result.stderr if CaptureStream.STDERR in capture else command_result.stdout
                    ),
                    datetime.datetime.now().isoformat(),
                )
                if original_output is None or current_output.output != original_output.output:
                    if original_output is not None:
                        yield original_output, current_output
                    original_output = current_output
            if once:
                break
            sleep(interval)
    except Interrupt:
        pass
    finally:
        signal.signal(signal.SIGINT, original_sigint_handler)
        signal.signal(signal.SIGTERM, original_sigterm_handler)
        if original_output is not None:
            save_command_output(original_output)
