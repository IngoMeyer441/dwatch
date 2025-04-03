import os
import subprocess
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple

from setuptools import Command, setup


class PyinstallerCommand(Command):  # type: ignore
    description = "create a self-contained executable with PyInstaller"
    user_options: List[Tuple[str, Optional[str], str]] = []

    def initialize_options(self) -> None:
        pass

    def finalize_options(self) -> None:
        pass

    def run(self) -> None:
        with TemporaryDirectory() as temp_dir:
            subprocess.check_call(["python3", "-m", "venv", os.path.join(temp_dir, "env")])
            subprocess.check_call(
                [os.path.join(temp_dir, "env/bin/pip"), "install", "--upgrade", "pip", "setuptools", "wheel"]
            )
            subprocess.check_call([os.path.join(temp_dir, "env/bin/pip"), "install", "."])
            subprocess.check_call([os.path.join(temp_dir, "env/bin/pip"), "install", "pyinstaller"])
            with open(os.path.join(temp_dir, "entrypoint.py"), "w") as f:
                f.write(
                    """
#!/usr/bin/env python3

from dwatch.cli import main


if __name__ == "__main__":
    main()
                    """.strip()
                )
            subprocess.check_call(
                [
                    os.path.join(temp_dir, "env/bin/pyinstaller"),
                    f"--add-data={os.path.join('dwatch', '*.jinja.*')}{os.pathsep}dwatch",
                    "--clean",
                    "--name=dwatch",
                    "--onefile",
                    "--strip",
                    os.path.join(temp_dir, "entrypoint.py"),
                ]
            )


setup(cmdclass={"bdist_pyinstaller": PyinstallerCommand})
