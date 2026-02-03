"""PDF/TXT/MD parsers placeholder."""


def parse_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# Add PDF/MD parsing helpers as needed
