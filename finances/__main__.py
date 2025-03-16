# Copyright Jamil RAICHOUNI and contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import os
import pathlib
import shlex
import shutil
import subprocess
import time

import click
import fasthtml.common as fh
import uvicorn

import finances
import finances.app
import finances.constants as c
from finances import core

logger = logging.getLogger(__package__)
core.setup_logging(logger, level="DEBUG")


if os.getenv("FIN_DEV_MODE", "0") == "1":
    _app_cls = fh.FastHTMLWithLiveReload
else:
    _app_cls = fh.FastHTML


app = finances.app.app


def _find_exe(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise SystemExit(f"Cannot find {name!r}, install it and try again")
    return path


def _install_npm_pkgs() -> None:
    npm = _find_exe("npm")
    cmd = [npm, "clean-install"]
    logger.info(shlex.join(cmd))
    subprocess.check_call(cmd)


def build_css(*, watch: bool) -> subprocess.Popen | None:
    """Build style sheet using Tailwind CSS."""
    _install_npm_pkgs()
    exe = shutil.which("node_modules/.bin/tailwindcss")
    if exe is None:
        raise SystemExit("tailwindcss failed to install, please try again")
    exe = os.path.realpath(exe)

    logger.info("Building style sheet...")
    tailwind_cmd = [
        exe,
        "--minify",
    ]
    if c.INPUT_CSS_PATH.is_file():
        tailwind_cmd.extend(
            [
                "--input",
                str(c.INPUT_CSS_PATH),
            ]
        )
    tailwind_cmd.extend(
        [
            "--output",
            str(c.MAIN_CSS_PATH),
        ]
    )
    if watch:
        tailwind_cmd.append("--watch")
        logger.info(shlex.join(tailwind_cmd))
        return subprocess.Popen(tailwind_cmd)

    logger.info(shlex.join(tailwind_cmd))
    subprocess.check_call(tailwind_cmd)
    return None


def run_local(host: str, port: int) -> None:
    """Run the application locally."""
    if not pathlib.Path(str(c.MAIN_CSS_PATH)).exists():
        build_css(watch=False)

    logger.info("Running the application locally...")
    uvicorn.run(
        app="finances.__main__:app",
        host=host,
        port=port,
    )


def run_local_dev(host: str, port: int) -> None:
    logger.info("Running the application locally with full reload...")
    os.environ["FIN_DEV_MODE"] = "1"
    tailwind_proc = build_css(watch=True)
    assert tailwind_proc is not None
    time.sleep(1)  # avoid direct uvicorn reload when css file is written

    try:
        with tailwind_proc:
            uvicorn.run(
                app="finances.__main__:app",
                host=host,
                port=port,
                reload=True,
                reload_dirs=[".", "/home/nerd/googledrive/JAR/finances"],
                reload_includes=["*.py", "*.yaml"],
                reload_excludes=["*.blob", "*.db"],
            )
    except KeyboardInterrupt:
        tailwind_proc.terminate()


@click.group()
@click.version_option(
    version=finances.__version__,
    prog_name="finances",
    message="%(prog)s %(version)s",
)
def main() -> None:
    """Console script for finances."""


@main.command()
@click.option(
    "--dev",
    is_flag=True,
    show_default=True,
    help="Launch in development mode with auto-reload.",
)
@click.option(
    "--host",
    envvar="FIN_HOST",
    default="0.0.0.0",
    show_default=True,
    help="The hostname or IP address to bind to.",
)
@click.option(
    "--port",
    envvar="FIN_PORT",
    default=8888,
    show_default=True,
    help="The port to listen on.",
)
def run(
    *,
    dev: bool,
    host: str,
    port: int,
) -> None:
    """Run the application."""
    if dev:
        run_local_dev(host, port)
    else:
        run_local(host, port)


if __name__ == "__main__":
    main()
