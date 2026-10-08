"""Fix corrupted UTF-8 sequences in all frontend CSS files."""
import pathlib

SRC = pathlib.Path(r"c:\Users\anike\aegis\AEGIS\frontend\src")

dq = b'"'
sq = b"'"

REPLACEMENTS = [
    (b"\xe2\x80\xa2", b""),    # bullet U+2022
    (b"\xe2\x80\x94", b"-"),   # em dash U+2014
    (b"\xe2\x80\x93", b"-"),   # en dash U+2013
    (b"\xe2\x80\x9c", dq),     # left double quote U+201C
    (b"\xe2\x80\x9d", dq),     # right double quote U+201D
    (b"\xe2\x80\x98", sq),     # left single quote U+2018
    (b"\xe2\x80\x99", sq),     # right single quote U+2019
]

fixed = []
for p in SRC.rglob("*.css"):
    raw = p.read_bytes()
    orig = raw
    for bad, good in REPLACEMENTS:
        raw = raw.replace(bad, good)
    if raw != orig:
        p.write_bytes(raw)
        fixed.append(p.name)

if fixed:
    print("Fixed:", fixed)
else:
    print("All CSS files were already clean")
