class DocstringState:
    """Tracks docstring parsing state for Python files"""

    def __init__(self):
        self.in_docstring = False
        self.docstring_delimiter = None

    def start_docstring(self, delimiter: str) -> None:
        """Start tracking a docstring"""
        self.in_docstring = True
        self.docstring_delimiter = delimiter

    def end_docstring(self) -> None:
        """End tracking a docstring"""
        self.in_docstring = False
        self.docstring_delimiter = None

    def is_matching_delimiter(self, delimiter: str) -> bool:
        """Check if delimiter matches current docstring delimiter"""
        return bool(self.in_docstring and delimiter == self.docstring_delimiter)


class BlockCommentState:
    """Tracks block comment parsing state for JavaScript/TypeScript files"""

    def __init__(self):
        self.in_block_comment = False

    def start_block_comment(self) -> None:
        """Start tracking a block comment"""
        self.in_block_comment = True

    def end_block_comment(self) -> None:
        """End tracking a block comment"""
        self.in_block_comment = False
