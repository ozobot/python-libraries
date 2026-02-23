from __future__ import annotations

from enum import Flag
from typing import Any

from sphinx.application import Sphinx
from sphinx.ext.autodoc import ClassDocumenter, Documenter
from sphinx.util.typing import ExtensionMetadata


# This is a slightly modified extension example from the Sphinx website: https://www.sphinx-doc.org/en/master/development/tutorials/autodoc_ext.html
# It formats enum.Flag members including aliases
def setup(app: Sphinx) -> ExtensionMetadata:
    app.setup_extension("sphinx.ext.autodoc")  # Require autodoc extension
    app.add_autodocumenter(EnumFlagDocumenter)

    return {
        "version": "1",
        "parallel_read_safe": True,
    }


class EnumFlagDocumenter(ClassDocumenter):
    objtype = "enumflag"
    directivetype = ClassDocumenter.objtype
    priority = 10 + ClassDocumenter.priority

    @classmethod
    def can_document_member(cls, member: Any, membername: str, isattr: bool, parent: Documenter) -> bool:
        try:
            return issubclass(member, Flag)
        except TypeError:
            return False

    def add_content(
        self,
        more_content,
    ) -> None:
        super().add_content(more_content)

        source_name = self.get_sourcename()
        enum_object: Flag = self.object
        self.add_line("", source_name)

        for the_member_name, enum_member in enum_object.__members__.items():  # type: ignore[attr-defined]
            members = list(enum_member)
            if len(members) == 1:
                the_member_value = repr(members[0])
            else:
                the_member_value = " | ".join([m.name for m in members])

            self.add_line(f"**{the_member_name}**: {the_member_value}", source_name)
            self.add_line("", source_name)
