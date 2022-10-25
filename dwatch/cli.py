import argparse
import logging
import os
import shlex
import sys
from typing import Optional

from yacl import setup_colored_stderr_logging

try:
    from yacl import setup_colored_exceptions

    has_setup_colored_exceptions = True
except ImportError:
    has_setup_colored_exceptions = False

from . import __version__
from .config import CONFIG_FILEPATH, Config, Verbosity, config
from .mail import MailError, send_mail
from .monitor import watch
from .render import TemplateType, render_template

logger = logging.getLogger(__name__)


def get_argumentparser() -> argparse.ArgumentParser:
    def add_bool_argument(
        parser: argparse.ArgumentParser, short_name: Optional[str], long_name: str, help: str
    ) -> None:
        normalized_long_name = long_name.replace("-", "_")
        group = parser.add_mutually_exclusive_group()
        flag_names = ["--" + long_name]
        if short_name is not None:
            flag_names.insert(0, "-" + short_name)
        group.add_argument(
            *flag_names,
            default=getattr(config, normalized_long_name),
            dest=normalized_long_name,
            action="store_true",
            help=help + ' (default: "{}")'.format(getattr(config, normalized_long_name)),
        )
        flag_names = ["--no-" + long_name]
        if short_name is not None:
            flag_names.insert(0, "-" + short_name.upper())
        group.add_argument(
            *flag_names,
            default=not getattr(config, normalized_long_name),
            dest=normalized_long_name,
            action="store_false",
            help="don't " + help[:1].lower() + help[1:] + ' (default: "%(default)s")',
        )

    parser = argparse.ArgumentParser(
        description="""
%(prog)s is a tool for watching command output for changes and notifiying the user.
Default values for command line options are taken from the config file at "{}"
""".format(
            CONFIG_FILEPATH
        ),
    )
    parser.add_argument(
        "-i",
        "--interval",
        action="store",
        default=config.interval,
        dest="interval",
        help='set the interval for the watched command (default: "%(default)s")',
    )
    add_bool_argument(
        parser,
        "o",
        "run-once",
        help="run the given command once and exit",
    )
    add_bool_argument(
        parser,
        "s",
        "shell",
        help="run the given command in a shell subprocess",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        dest="print_on_stdout",
        help="print the diff on stdout, do not send a mail",
    )
    parser.add_argument(
        "-V", "--version", action="store_true", dest="print_version", help="print the version number and exit"
    )
    parser.add_argument(
        "-w",
        "--write-default-config",
        action="store_true",
        dest="write_default_config",
        help='create a configuration file with default values (config filepath: "{}")'.format(CONFIG_FILEPATH),
    )
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        dest="quiet",
        help='be quiet (default: "{}")'.format(config.verbosity is Verbosity.QUIET),
    )
    verbosity_group.add_argument(
        "--error",
        action="store_true",
        dest="error",
        help='print error messages (default: "{}")'.format(config.verbosity is Verbosity.ERROR),
    )
    verbosity_group.add_argument(
        "--warn",
        action="store_true",
        dest="warn",
        help='print warning and error messages (default: "{}")'.format(config.verbosity is Verbosity.WARN),
    )
    verbosity_group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        help='be verbose (default: "{}")'.format(config.verbosity is Verbosity.VERBOSE),
    )
    verbosity_group.add_argument(
        "--debug",
        action="store_true",
        dest="debug",
        help='print debug messages (default: "{}")'.format(config.verbosity is Verbosity.DEBUG),
    )
    parser.add_argument("command", nargs="?", help="the command to watch")
    return parser


def parse_arguments() -> argparse.Namespace:
    parser = get_argumentparser()
    args = parser.parse_args()
    if args.print_version:
        return args
    args.verbosity_level = (
        Verbosity.QUIET
        if args.quiet
        else Verbosity.ERROR
        if args.error
        else Verbosity.WARN
        if args.warn
        else Verbosity.VERBOSE
        if args.verbose
        else Verbosity.DEBUG
        if args.debug
        else config.verbosity
    )
    return args


def setup_stderr_logging(verbosity_level: Verbosity) -> None:
    if verbosity_level == Verbosity.QUIET:
        logging.getLogger().handlers = []
    elif verbosity_level == Verbosity.ERROR:
        logging.basicConfig(level=logging.ERROR)
    elif verbosity_level == Verbosity.WARN:
        logging.basicConfig(level=logging.WARNING)
    elif verbosity_level == Verbosity.VERBOSE:
        logging.basicConfig(level=logging.INFO)
    elif verbosity_level == Verbosity.DEBUG:
        logging.basicConfig(level=logging.DEBUG)
    else:
        raise NotImplementedError('The verbosity level "{}" is not implemented'.format(verbosity_level))
    if not verbosity_level == Verbosity.QUIET:
        setup_colored_stderr_logging(format_string="[%(levelname)s] %(message)s")


def handle_monitoring(args: argparse.Namespace) -> None:
    if args.shell:
        command = [args.command]
    else:
        command = shlex.split(args.command)
    for original_command_output, compare_command_output in watch(command, args.shell, args.run_once, args.interval):
        if args.print_on_stdout:
            logger.info("Write command diff to stdout:")
            report_plain = render_template(
                TemplateType.PLAIN, args.command, original_command_output, compare_command_output
            )
            print(report_plain)
            print()
        else:
            logger.info("Generate an HTML diff and send a mail")
            send_mail(
                args.command,
                original_command_output,
                compare_command_output,
                config.mail_backend,
                config.mail_from_address,
                config.mail_to_addresses,
                config.mail_server,
                config.mail_encryption,
                config.mail_login_user,
                config.mail_login_password,
            )


def main() -> None:
    expected_exceptions = (MailError,)
    try:
        args = parse_arguments()
        if args.print_version:
            print("{}, version {}".format(os.path.basename(sys.argv[0]), __version__))
            sys.exit(0)
        if has_setup_colored_exceptions:
            setup_colored_exceptions(True)
        setup_stderr_logging(args.verbosity_level)
        if args.write_default_config:
            Config.write_default_config()
            logger.info('Wrote a default config file to "%s"', CONFIG_FILEPATH)
            sys.exit(0)
        handle_monitoring(args)
    except expected_exceptions as e:
        logger.error(str(e))
        for i, exception_class in enumerate(expected_exceptions, start=3):
            if isinstance(e, exception_class):
                sys.exit(i)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
    sys.exit(0)
