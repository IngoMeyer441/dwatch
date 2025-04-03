# dwatch

## Overview

![example_report](https://raw.githubusercontent.com/IngoMeyer441/dwatch/master/example_report.png)

dwatch (*diff watch*) is a tool to monitor the output of a given command and notify the user on changes by sending an
email with a diff view.

## Installation

dwatch is available on PyPI and can be installed with `pip`:

```bash
python3 -m pip install dwatch
```

At least Python 3.9 is required.

If you run an Arch-based system, you can also install `dwatch` from the
[AUR](https://aur.archlinux.org/packages/dwatch/):

```bash
yay -S dwatch
```

You can also download self-contained executables (no Python installation required) for Linux x64, macOS x64 and macOS
ARM64 from the [releases page](https://github.com/IngoMeyer441/dwatch/releases).

## Usage

By default, dwatch runs a commmand passed on the command line every 60 seconds and notifies the user on any changes. You
can run a first test with:

```bash
dwatch -i 2 --stdout "date"
```

This runs the `date` command every 2 seconds and prints the output differences to stdout.

Pass the `--run-once` option to run one check, print a diff if necessary and exit. The diff is created against the
output from the previous run (command outputs are stored in the file `~/.dwatch_command_output.json`). This is
especially useful in cron jobs.

Without `--stdout` the diff output is sent as an HTML email. By default, dwatch uses the `sendmail` tool for this, which
is available if a local email server like Postfix or Exim is installed or if a simple mail forwarder like
[ssmtp](https://packages.debian.org/stable/ssmtp) is present. As an alternative, dwatch supports direct communication
with a mail server with Python's builtin [smtplib](https://docs.python.org/3/library/smtplib.html). This can be used if
no email server is installed locally. In either case, run

```bash
dwatch --write-default-config
```

to create a default configuration file at `~/.dwatchrc`. Open the file with a text editor and configure a sender
`from_address` and receiver `to_address` in the `[mail]` section:

```text
[mail]
backend = sendmail
server = mail.example.com
login_user = jane.doe
login_password = xxx
encryption = starttls
from_address = dwatch-report@example.com
to_addresses = admin@example.com
```

Change `sendmail` to `smtplib` to use an arbitrary email provider and set the server address, the login credentials and
the encryption (`none`, `starttls` or `ssl`). If `none` is chosen, no login credentials are sent for security reasons.
This can only be used for very simple mail server setups.

Use the `--description` command line option with a text argument to add a description to the diff report and the subject
field of emails. This can be useful to distinguish different commands.

## Configuration

These options can be configured in the file `~/.dwatchrc`:

- `[general]` section:

  - `verbosity`: The logging level of the application. Can be one of `quiet`, `error`, `warn`, `verbose` or `debug`.

- `[mail]` section:

  - `backend`: `sendmail` to use the local `sendmail` command or `smtplib` to connect to an arbitrary email server with
    the smtp protocol.
  - `server`: The mail server to use. This field is ignored if the `sendmail` backend is chosen.
  - `login_user`: The login name for the mail server. This field is ignored if the `sendmail` backend is chosen.
  - `login_password`: The login password for the mail server. This field is ignored if the `sendmail` backend is chosen.
  - `encryption`: The encryption to use to connect to the mail server, can be `none` (not recommended!), `starttls` or
    `ssl`. This field is ignored if the `sendmail` backend is chosen. If `none` is chosen, no login credentials are sent
    for security reasons.
  - `from_address`: The from address in the email envelope. Many providers do not support to change the from address and
    overwrite this with your actual mail address.
  - `to_address`: The recipient address.

- `[watch]` section:

  - `abort_on_error`: If set to `True`, the program will abort if the given command exits with a non-zero exit code.
  - `capture`: The streams to capture from, as comma-separated list of "stdout" and "stderr".
  - `ignore_output_on_error`: Ignore the output of the executed command if it exits with a non-zero exit code.
  - `interval`: The time interval in seconds between runs of the given command.
  - `run_once`: If set to `True`, the command will only be run once the program exits. This is intended to be used with
    cron jobs.
  - `shell`: Run the given command in a subshell. This is useful to allow shell patterns in a command like pipes (for
    example `command | grep pattern`).

## Command line options

```text
usage: dwatch [-h] [-a | -A] [-c CAPTURE] [-d DESCRIPTION] [-i INTERVAL] [-l |
              -L] [-o | -O] [-s | -S] [--stdout] [-V] [-w] [-x | -X] [-q |
              --error | --warn | -v | --debug]
              [command]

dwatch is a tool for watching command output for changes and notifiying the
user. Default values for command line options are taken from the config file
at "~/.dwatchrc"

positional arguments:
  command               the command to watch

options:
  -h, --help            show this help message and exit
  -a, --abort-on-error  abort if the executed command exits with a non-zero
                        exit code (default: "False")
  -A, --no-abort-on-error
                        don't abort if the executed command exits with a non-
                        zero exit code (default: "True")
  -c, --capture CAPTURE
                        set the streams to capture from, as comma-separated
                        list of "stdout" and "stderr" (default:
                        "stdout,stderr")
  -d, --description DESCRIPTION
                        add a description which is added to the diff output
                        and used in the e-mail subject
  -i, --interval INTERVAL
                        set the interval for the watched command (default:
                        "60.0")
  -l, --wait-for-lock   block until other instances of dwatch are done
                        (default: "True")
  -L, --no-wait-for-lock
                        don't block until other instances of dwatch are done
                        (default: "False")
  -o, --run-once        run the given command once and exit (default: "False")
  -O, --no-run-once     don't run the given command once and exit (default:
                        "True")
  -s, --shell           run the given command in a shell subprocess (default:
                        "False")
  -S, --no-shell        don't run the given command in a shell subprocess
                        (default: "True")
  --stdout              print the diff on stdout, do not send a mail
  -V, --version         print the version number and exit
  -w, --write-default-config
                        create a configuration file with default values
                        (config filepath: "~/.dwatchrc")
  -x, --ignore-output-on-error
                        ignore the output of the executed command if it exits
                        with a non-zero exit code (default: "False")
  -X, --no-ignore-output-on-error
                        don't ignore the output of the executed command if it
                        exits with a non-zero exit code (default: "True")
  -q, --quiet           be quiet (default: "False")
  --error               print error messages (default: "False")
  --warn                print warning and error messages (default: "False")
  -v, --verbose         be verbose (default: "True")
  --debug               print debug messages (default: "False")
```
