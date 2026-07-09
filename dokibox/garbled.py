# -*- coding: utf-8 -*-
"""Generate random garbled text with diacritics and special Latin characters."""
import random


_POOL = (
    # lowercase with diacritics
    "àáâãäåāăąǎȁȃạảấầẩẫậắằẳẵặ"
    "èéêëēėęěȅȇẹẻẽếềểễệ"
    "ìíîïĩīįǐȉȋịỉ"
    "òóôõöøōőơǒȍȏọỏốồổỗộớờởỡợ"
    "ùúûüũūųűǔȕȗụủứừửữự"
    "ýÿŷȳỳỵỷỹ"
    # consonants with diacritics
    "çćĉċč"
    "ďđ"
    "ĝğġģ"
    "ĥħ"
    "ĵ"
    "ķ"
    "ĺļľŀł"
    "ñńņňŉŋ"
    "ŕŗř"
    "śŝşš"
    "ţťŧ"
    "ŵ"
    "źżž"
    # special ligatures / extra
    "æǽǣ"
    "œ"
    "ß"
    "þð"
    # uppercase with diacritics
    "ÀÁÂÃÄÅĀĂĄǺẠẢẤẦẨẪẬẮẰẲẴẶ"
    "ÈÉÊËĒĖĘẸẺẼẾỀỂỄỆ"
    "ÌÍÎÏĨĪĮỊỈ"
    "ÒÓÔÕÖØŌŐỌỎỐỒỔỖỘỚỜỞỠỢ"
    "ÙÚÛÜŨŪŲŮŰỤỦỨỪỬỮỰ"
    "ÝŸŶỲỴỶỸ"
    "ÇĆĈĊČ"
    "ÑŃŅŇŊ"
    "Æ"
    "Œ"
    "Þ"
    # combining diacritical marks (tone marks etc.)
    "\u0300\u0301\u0302\u0303\u0304\u0306\u0307\u0308\u0309"
    "\u030a\u030b\u030c\u030f\u0311\u031b\u0323\u0324\u0326"
    "\u0327\u0328\u032d\u032e\u0330\u0331\u0342\u0344"
    ""
    " "
    "☒"
    "*&^%$#@!"
    "æ¯è¿æ ·ç"
    "⯐"
)


def garbled(n: int = 200) -> str:
    """Generate a string of n random characters with diacritics and special Latin symbols.

    Args:
        n: desired length of the output string (default 200).

    Returns:
        A string of n random characters that looks like garbled Latin text.
    """
    return ''.join(random.choice(_POOL) for _ in range(n))
