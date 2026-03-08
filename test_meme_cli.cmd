@echo off
chcp 65001 >nul
echo ======================================================================
echo TEST PIPELINE MEME - Diagnostic CLI
echo ======================================================================
echo.

cd /d %~dp0

REM ======================================================================
REM TEST 1 : detmeme.py - Parsing de la syntaxe
REM ======================================================================
echo [TEST 1] detmeme.py - Parsing syntaxe
echo ----------------------------------------------------------------------
echo.
echo Test 1.1: "meme nom que Guillaume Moulin"
python detmeme.py "meme nom que Guillaume Moulin"
echo.
echo ----------------------------------------------------------------------
echo Test 1.2: "meme portrait et meme nom que Guillaume Moulin"
python detmeme.py "meme portrait et meme nom que Guillaume Moulin"
echo.

pause

REM ======================================================================
REM TEST 2 : trouveid.py - Resolution nom vers ID
REM ======================================================================
echo.
echo [TEST 2] trouveid.py - Resolution nom vers ID
echo ----------------------------------------------------------------------
echo.
echo Test 2.1: Enrichissement JSON avec reference par nom
python trouveid.py bases\base1000.db "{\"criteres\":[{\"type\":\"meme\",\"cible\":\"nom\",\"label\":\"Meme nom\",\"valeur\":null}],\"reference\":{\"type\":\"nom\",\"valeur\":\"Guillaume Moulin\",\"id\":null}}" --verbose
echo.

pause

REM ======================================================================
REM TEST 3 : jsonsql.py - Generation SQL
REM ======================================================================
echo.
echo [TEST 3] jsonsql.py - Generation SQL
echo ----------------------------------------------------------------------
echo.
echo Test 3.1: JSON avec reference_id et reference_patient
python jsonsql.py "{\"criteres\":[{\"type\":\"meme\",\"cible\":\"nom\",\"label\":\"Meme nom\",\"valeur\":null,\"reference_id\":2,\"reference_patient\":{\"id\":2,\"prenom\":\"Guillaume\",\"nom\":\"Moulin\",\"sexe\":\"M\",\"age\":19}}]}" --debug
echo.

pause

REM ======================================================================
REM TEST 4 : trouve.py - Pipeline complet
REM ======================================================================
echo.
echo [TEST 4] trouve.py - Pipeline complet
echo ----------------------------------------------------------------------
echo.
echo Test 4.1: "meme nom que Guillaume Moulin"
python trouve.py bases\base1000.db "meme nom que Guillaume Moulin" --verbose
echo.
echo ----------------------------------------------------------------------
echo Test 4.2: "meme portrait que Guillaume Moulin"
python trouve.py bases\base1000.db "meme portrait que Guillaume Moulin" --verbose
echo.

pause

echo.
echo ======================================================================
echo FIN DES TESTS
echo ======================================================================
