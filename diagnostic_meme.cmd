@echo off
chcp 65001 >nul
REM diagnostic_meme.cmd - Diagnostic minimal du pipeline
REM Date: 22/01/2026

echo ======================================================================
echo DIAGNOSTIC PIPELINE MEME
echo ======================================================================
echo.

set BASE=bases\base25000.db

echo [1] Version jsonsql.py:
python -c "from jsonsql import __version__; print(f'   Version: {__version__}')"
echo.

echo [2] Guillaume Moulin dans la base:
python -c "import sqlite3; conn=sqlite3.connect('%BASE%'); c=conn.cursor(); c.execute('SELECT id, prenom, nom, idportrait FROM patients WHERE id=2'); r=c.fetchone(); print(f'   ID={r[0]}, {r[1]} {r[2]}, idportrait={r[3]}')"
echo.

echo [3] Test jsonsql.py direct - SQL genere:
python -c "import json; from jsonsql import generer_sql; j={'criteres':[{'type':'meme','cible':'portrait','reference_id':2,'reference_patient':{'id':2,'idportrait':'29'}}]}; r=generer_sql(j); print(f'   SQL: {r[\"sql\"][:100]}...'); print(f'   Params: {r[\"params\"]}'); print(f'   Contient p.id!=? : {\"p.id !=\" in r[\"sql\"] or \"p.id!=\" in r[\"sql\"]}')"
echo.

echo [4] Test pipeline complet trouve.py:
python -c "from trouve import rechercher; r=rechercher('meme portrait que Guillaume Moulin', '%BASE%', verbose=False); print(f'   Nb resultats: {r[\"nb\"]}'); ids=r.get('ids',[]); print(f'   ID 2 present: {2 in ids}'); print(f'   10 premiers IDs: {ids[:10]}')"
echo.

echo [5] Patients avec idportrait=29 (SQL direct):
python -c "import sqlite3; conn=sqlite3.connect('%BASE%'); c=conn.cursor(); c.execute('SELECT id, prenom, nom FROM patients WHERE idportrait=\"29\" ORDER BY id LIMIT 5'); print('   ' + str([f'{r[0]}:{r[1]} {r[2]}' for r in c.fetchall()]))"
echo.

pause
