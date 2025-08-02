import re
import string
import unicodedata

def clean_text(
        text: str,
        lowercase: bool =  True,
        remove_non_ascii: bool =  True,
        remove_punctuation: bool = False,
        collapse_whitespace: bool =  True,
) -> str:
    """
    Cleans the input text based on specified parameters.

    Args:
        text (str): The input text to clean.
        lowercase (bool): If True, convert text to lowercase.
        remove_non_ascii (bool): If True, remove non-ASCII characters.
        remove_punctuation (bool): If True, remove punctuation characters.
        collapse_whitespace (bool): If True, collapse multiple whitespace into a single space.

    Returns:
        str: The cleaned text.
    """
    if not isinstance(text, str):
        return ""
    
    text = unicodedata.normalize("NFKC", text)

    if lowercase:
        text = text.lower()
    
    if remove_non_ascii:
        text = text.encode("ascii", errors="ignore").decode("ascii")  

    if remove_punctuation:
        translator = str.maketrans("" , "" , string.punctuation)
        text = text.translate(translator)

    
    if collapse_whitespace:
        text = re.sub(r'\s+', ' ', text) 
    
    return text.strip()

# indha cleaning lam onnum agala na! 
def remove_control_chars (text: str) ->str : 
    """Strip non printable characters from text."""
    return "".join(ch for ch in text if ch.isprintable() or ch.isspace())

# enaku therija testing 
if __name__ == "__main__":
    sample_text = "PODU IDHU dhan sample text!!\n          EXTRA&*)@*$# SPACE LAMM!!, \tpunctuation oda and enaku ThrINja unicode--lam--.."
    print("Original text:", sample_text)
    cleaned = clean_text(sample_text, lowercase=True, remove_non_ascii=False, remove_punctuation=False, collapse_whitespace=True)
    print("cleaned", cleaned)
    cleaned_no_controls = remove_control_chars(cleaned)
    print("cleaned_no_controls", cleaned_no_controls)