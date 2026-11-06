"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
import pytest

from crud.lexer import tokenize, LexError, TokenType as T


def test_regresi_operator_tidak_sama_satu_token():
    toks = tokenize("a <> 1")
    assert [t.value for t in toks[:3]] == ["a", "<>", "1"]
    