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
from crud.analyzer import analyze_statement


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

def test_regresi_alias_delete_tidak_bocor_ke_statement_berikutnya():
    script = parse_sql("DELETE FROM sesi s WHERE s.a = 1; SELECT s.id FROM pengguna u")
    r = Resolver()
    diags = r.resolve_script(script)
    assert r.scope is None
    assert [d.level for d in diags] == ["error"]
    assert "'s'" in diags[0].message

def test_tepi_kolom_tanpa_qualifier_dua_tabel_ambigu():
    script = parse_sql(
        "SELECT nama FROM pelanggan p JOIN pesanan o ON o.pelanggan_id = p.id")
    diags = Resolver().resolve_script(script)
    nama = [c for c in ast.iter_nodes(script)
            if isinstance(c, ast.ColumnRef) and c.name == "nama"][0]
    assert nama.resolved is None
    assert [d.level for d in diags] == ["warning"]

def test_tepi_kolom_tanpa_qualifier_hanya_melihat_scope_terdalam():
    script = parse_sql(
        "SELECT p.id FROM pelanggan p "
        "WHERE EXISTS (SELECT 1 FROM pesanan o WHERE total > 0)")
    Resolver().resolve_script(script)
    total = [c for c in ast.iter_nodes(script)
             if isinstance(c, ast.ColumnRef) and c.name == "total"][0]
    assert total.resolved == "pesanan"

def test_regresi_update_subquery_dibaca_bukan_diubah():
    script = parse_sql(
        "UPDATE a SET x = (SELECT MAX(y) FROM b) WHERE id IN (SELECT id FROM c)")
    assert analyze_statement(script.statements[0]) == {
        "a": {"U"}, "b": {"R"}, "c": {"R"}}

def test_regresi_presedensi_and_lebih_tinggi_dari_or():
    script = parse_sql("SELECT 1 FROM t WHERE a = 1 OR b = 2 AND c = 3")
    where = script.statements[0].where
    assert where.op == "OR"
    assert where.right.op == "AND"

def test_regresi_recovery_lanjut_ke_statement_berikutnya():
    script = parse_sql(
        "SELECT FROM a; DELETE FROM b; SELECT FROM c; UPDATE d SET x = 1")
    assert len(script.errors) == 2
    assert [type(s).__name__ for s in script.statements] == ["Delete", "Update"]