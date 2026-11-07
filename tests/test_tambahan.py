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
from crud.analyzer import column_usage


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
    # Kolom tanpa qualifier berisiko dianggap berasal dari tabel yang salah ketika ada beberapa tabel.
    script = parse_sql(
        "SELECT nama FROM pelanggan p JOIN pesanan o ON o.pelanggan_id = p.id"
    )
    assert script.errors == []

    diags = Resolver().resolve_script(script)
    nama = [
        c for c in ast.iter_nodes(script)
        if isinstance(c, ast.ColumnRef) and c.name == "nama"
    ]

    assert len(nama) == 1
    assert nama[0].resolved is None
    assert len(diags) == 1
    assert diags[0].level == "warning"
    assert "ambigu" in diags[0].message.lower()

def test_tepi_kolom_tanpa_qualifier_hanya_melihat_scope_terdalam():
    # Kolom dalam subquery berisiko salah dihubungkan ke tabel milik query luar.
    script = parse_sql(
        "SELECT p.id FROM pelanggan p "
        "WHERE EXISTS (SELECT 1 FROM pesanan o WHERE total > 0)"
    )
    assert script.errors == []

    diags = Resolver().resolve_script(script)

    total = [
        c for c in ast.iter_nodes(script)
        if isinstance(c, ast.ColumnRef) and c.name == "total"
    ]

    assert len(total) == 1
    assert diags == []
    assert total[0].resolved == "pesanan"

def test_tepi_penanda_komentar_di_dalam_string_bukan_komentar():
    # Isi string yang menyerupai komentar tidak boleh dibaca sebagai komentar.
    toks = tokenize("'a -- b' '/* x */'")

    assert [(t.type, t.value) for t in toks[:-1]] == [
        (T.STRING, "a -- b"),
        (T.STRING, "/* x */"),
    ]

def test_tepi_subquery_from_tanpa_alias():
    script = parse_sql("SELECT nama FROM (SELECT nama FROM pelanggan)")
    r = Resolver()
    diags = r.resolve_script(script)
    assert any("tanpa alias" in d.message.lower() for d in diags)

def test_tepi_subquery_akses_scope_luar():
    script = parse_sql(
        "SELECT p.id FROM pelanggan p WHERE p.id IN (SELECT o.pelanggan_id FROM pesanan o WHERE o.total > p.id)")
    r = Resolver()
    diags = r.resolve_script(script)
    assert diags == []
    cols = [c for c in ast.iter_nodes(script) if isinstance(c, ast.ColumnRef)]

    correlated_col = [c for c in cols if c.qualifier == "p" and c.resolved == "pelanggan"]
    assert len(correlated_col) > 0

def test_regresi_kolom_tanpa_qualifier_derived_table():
    script = parse_sql("SELECT nama FROM (SELECT nama, id FROM pelanggan) AS sub")
    Resolver().resolve_script(script)
    cols = [c for c in ast.iter_nodes(script) if isinstance(c, ast.ColumnRef)]
    assert [c.resolved for c in cols] == [None, "pelanggan", "pelanggan"]

def test_regresi_kolom_derived_table_analyzer():
    script, diags = parse_sql("SELECT sub.nama FROM (SELECT nama FROM pelanggan) AS sub"), []
    script = parse_sql("SELECT sub.nama FROM (SELECT nama FROM pelanggan) AS sub")
    Resolver().resolve_script(script)

    cols = column_usage(script.statements[0])
    assert cols == {('pelanggan', 'nama', 'R')}

def test_parser_error_statement():
    script = parse_sql("SELECT FROM; SELECT * FROM produk;")

    assert len(script.errors) > 0
    assert len(script.statements) == 0

def test_parser_expression_perbandingan():
    script = parse_sql("SELECT * FROM produk WHERE harga BETWEEN 1000 AND 5000 AND diskon IS NOT NULL;")
    assert len(script.statements) == 1
    stmt = script.statements[0]
    
    assert stmt.where is not None
    assert isinstance(stmt.where, ast.BinaryOp)
    where_str = str(stmt.where).upper()
    assert "ISNULL" in where_str
    assert "NEGATED=TRUE" in where_str
