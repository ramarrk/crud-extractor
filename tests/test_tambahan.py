"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
import pytest

from crud.lexer import tokenize, LexError, TokenType as T
from crud.resolver import Resolver
from crud.parser import parse_sql
from crud import ast_nodes as ast


def test_regresi_operator_tidak_sama_satu_token():
    toks = tokenize("a <> 1")
    assert [t.value for t in toks[:3]] == ["a", "<>", "1"]

def test_regresi_kutip_ganda_dalam_string():
    toks = tokenize("'Rif''q'")
    assert [(t.type, t.value) for t in toks[:-1]] == [(T.STRING, "Rif'q")]

def test_regresi_keyword_campuran_huruf():
    toks = tokenize("select Select SELECT")
    assert all(t.type == T.KEYWORD and t.value == "SELECT" for t in toks[:3])

def test_regresi_alias_subquery_menutupi_alias_luar():
    script = parse_sql(
        "SELECT p.id FROM pelanggan p WHERE p.id IN (SELECT p.id FROM pesanan p)")
    Resolver().resolve_script(script)
    cols = [c for c in ast.iter_nodes(script) if isinstance(c, ast.ColumnRef)]
    assert [c.resolved for c in cols] == ["pelanggan", "pelanggan", "pesanan"]