import logging
import os
from difflib import HtmlDiff, unified_diff
from enum import Enum, auto
from typing import Optional

import jinja2

from .monitor import CommandOutput

NUM_CONTEXT_LINES = 3
HTML_TABSIZE = 4
HTML_WRAPCOLUMN = 120

HTML_TEMPLATE_FILENAME = "report_template.jinja.html"
PLAIN_TEMPLATE_FILENAME = "report_template.jinja.txt"

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    HTML = auto()
    PLAIN = auto()


def render_template(
    template_type: TemplateType,
    command: str,
    original_command_output: CommandOutput,
    compare_command_output: CommandOutput,
    description: Optional[str] = None,
) -> str:
    template = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__))).get_template(
        HTML_TEMPLATE_FILENAME if template_type is TemplateType.HTML else PLAIN_TEMPLATE_FILENAME
    )
    jinja_data = {
        "command": command.strip(),
        "original_text": original_command_output.output.rstrip(),
        "compare_text": compare_command_output.output.rstrip(),
        "description": description,
    }
    if template_type is TemplateType.HTML:
        logging.debug("Render HTML diff")
        html_diff = HtmlDiff(tabsize=HTML_TABSIZE, wrapcolumn=HTML_WRAPCOLUMN)
        html_table = html_diff.make_table(
            original_command_output.output.splitlines(keepends=True),
            compare_command_output.output.splitlines(keepends=True),
            fromdesc="previous command output",
            todesc="current command output",
            context=True,
            numlines=NUM_CONTEXT_LINES,
        )
        jinja_data["diff_table"] = html_table
    else:
        logging.debug("Render a plain unified diff")
        diff_lines = unified_diff(
            original_command_output.output.splitlines(keepends=True),
            compare_command_output.output.splitlines(keepends=True),
            fromfile="previous command output",
            tofile="current command output",
            fromfiledate=original_command_output.timestamp,
            tofiledate=compare_command_output.timestamp,
            n=NUM_CONTEXT_LINES,
        )
        jinja_data["diff_lines"] = "".join(diff_lines).rstrip()
    return str(template.render(jinja_data))
