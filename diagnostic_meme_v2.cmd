@echo off
chcp 65001 >nul
REM diagnostic_meme_v2.cmd - Diagnostic avec chemin absolu
REM Date: 22/01/2026

echo ======================================================================
echo DIAGNOSTIC PIPELINE MEME v2
echo ======================================================================
echo.

set BASE=C:\cx\bases\base25000.db

echo Base: %BASE%
echo.

echo [1] Version jsonsql.py:
python -c "from jsonsql import __version__; print(f'   Version: {__version__}')"
echo.

echo [2] Guillaume Moulin dans la base:
python -c "import sqlite3; conn=sqlite3.connect(r'%BASE%'); c=conn.cursor(); c.execute('SELECT id, prenom, nom, idportrait FROM patients WHERE id=2'); r=c.fetchone(); print(f'   ID={r[0]}, {r[1]} {r[2]}, idportrait={r[3]}')"
echo.

echo [3] Test jsonsql.py direct - SQL genere:
python -c "import json; from jsonsql import generer_sql; j={'criteres':[{'type':'meme','cible':'portrait','reference_id':2,'reference_patient':{'id':2,'idportrait':'29'}}]}; r=generer_sql(j,debug=True); print(f'   Params: {r[\"params\"]}')"
echo.

echo [4] Test pipeline complet trouve.py (chemin absolu):
python -c "from trouve import rechercher; r=rechercher('meme portrait que Guillaume Moulin', r'%BASE%', verbose=True, debug=True); print(f'   Nb resultats: {r[\"nb\"]}'); ids=r.get('ids',[]); print(f'   ID 2 present: {2 in ids}'); print(f'   10 premiers IDs: {ids[:10]}')"
echo.

echo [5] Patients avec idportrait=29:
python -c "import sqlite3; conn=sqlite3.connect(r'%BASE%'); c=conn.cursor(); c.execute('SELECT id, prenom, nom FROM patients WHERE idportrait=\"29\" ORDER BY id LIMIT 10'); print('   Patients: ' + str([f'{r[0]}:{r[1]} {r[2]}' for r in c.fetchall()]))"
echo.

echo [6] Compter patients avec idportrait=29:
python -c "import sqlite3; conn=sqlite3.connect(r'%BASE%'); c=conn.cursor(); c.execute('SELECT COUNT(*) FROM patients WHERE idportrait=\"29\"'); print(f'   Total: {c.fetchone()[0]}')"
echo.

pause
