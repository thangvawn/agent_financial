#!/usr/bin/env python3
"""
CodeGraph Explorer CLI
Fast AST & Call-Graph inspection querying .codegraph/codegraph.db
Usage:
    python3 scripts/codegraph_explore.py <symbol_or_keyword> [--limit 10]
    python3 scripts/codegraph_explore.py --callers <function_name>
    python3 scripts/codegraph_explore.py --file <file_path>
"""
import sys
import sqlite3
import os
import json

DB_PATH = os.path.join(os.getcwd(), ".codegraph", "codegraph.db")

def get_connection():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found. Project is not indexed by CodeGraph.")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def search_symbols(query, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    # Search by exact name or substring
    sql = """
        SELECT id, kind, name, qualified_name, file_path, start_line, end_line, signature, docstring
        FROM nodes
        WHERE name LIKE ? OR qualified_name LIKE ?
        ORDER BY CASE WHEN name = ? THEN 0 ELSE 1 END, start_line
        LIMIT ?
    """
    pattern = f"%{query}%"
    cursor.execute(sql, (pattern, pattern, query, limit))
    rows = cursor.fetchall()
    
    if not rows:
        print(f"No symbols found matching '{query}'.")
        return

    print(f"=== Found {len(rows)} symbols matching '{query}' ===")
    for r in rows:
        print(f"\n[{r['kind'].upper()}] {r['qualified_name']}")
        print(f"  File: {r['file_path']} (lines {r['start_line']}-{r['end_line']})")
        if r['signature']:
            print(f"  Signature: {r['signature']}")
        if r['docstring']:
            first_line = r['docstring'].strip().split('\n')[0]
            print(f"  Doc: {first_line}")
        
        # Check callers
        cursor.execute("""
            SELECT n.qualified_name, n.file_path, e.kind, e.line
            FROM edges e
            JOIN nodes n ON e.source = n.id
            WHERE e.target = ?
            LIMIT 5
        """, (r['id'],))
        callers = cursor.fetchall()
        if callers:
            print("  Referenced/Called by:")
            for c in callers:
                print(f"    <- {c['qualified_name']} ({c['file_path']}:{c['line']}) [{c['kind']}]")

def list_file_symbols(file_path):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT kind, name, qualified_name, start_line, end_line, signature
        FROM nodes
        WHERE file_path LIKE ?
        ORDER BY start_line
    """, (f"%{file_path}%",))
    rows = cursor.fetchall()
    print(f"=== Symbols in '{file_path}' ({len(rows)} found) ===")
    for r in rows:
        print(f"L{r['start_line']:03d}-{r['end_line']:03d} [{r['kind'][:4].upper()}] {r['name']} - {r['signature'] or ''}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    arg = sys.argv[1]
    if arg == "--file" and len(sys.argv) > 2:
        list_file_symbols(sys.argv[2])
    else:
        search_symbols(arg)
