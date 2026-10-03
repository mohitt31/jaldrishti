"""Read PDF text while releasing native page and text handles deterministically."""

def page_text(document, index):
    page = document[index]
    try:
        text = page.get_textpage()
        try:
            return text.get_text_range()
        finally:
            text.close()
    finally:
        page.close()
