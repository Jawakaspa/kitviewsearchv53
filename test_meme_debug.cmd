@echo off
chcp 65001 >nul
REM test_meme_debug.cmd - Tests unitaires pipeline "même" sur base25000
REM Date: 22/01/2026

echo ======================================================================
echo TEST PIPELINE MEME - Debug base25000
echo ======================================================================
echo.

set BASE=bases\base25000.db
set QUESTION_PORTRAIT=meme portrait que Guillaume Moulin
set QUESTION_SEXE=meme sexe que Guillaume Moulin
set QUESTION_AGE=meme age que Guillaume Moulin

echo Base utilisée: %BASE%
echo.

echo [TEST 1] Vérifier que Guillaume Moulin existe dans la base
echo ----------------------------------------------------------------------
echo.
sqlite3 %BASE% "SELECT id, prenom, nom, sexe, age, idportrait FROM patients WHERE prenom='Guillaume' AND nom='Moulin';"
echo.
pause

echo [TEST 2] detmeme.py - Parsing "même portrait que Guillaume Moulin"
echo ----------------------------------------------------------------------
echo.
python detmeme.py "%QUESTION_PORTRAIT%" --debug
echo.
pause

echo [TEST 3] trouveid.py - Résolution nom vers ID
echo ----------------------------------------------------------------------
echo.
echo JSON d'entrée (simulé) :
echo {"criteres": [{"type": "meme", "cible": "portrait", "label": "Même portrait", "valeur": null}], "reference": {"type": "nom", "valeur": "Guillaume Moulin", "id": null}}
echo.
python trouveid.py %BASE% "{\"criteres\": [{\"type\": \"meme\", \"cible\": \"portrait\", \"label\": \"Même portrait\", \"valeur\": null}], \"reference\": {\"type\": \"nom\", \"valeur\": \"Guillaume Moulin\", \"id\": null}}" --verbose --debug
echo.
pause

echo [TEST 4] jsonsql.py - Génération SQL (avec reference_id et reference_patient)
echo ----------------------------------------------------------------------
echo.
echo JSON d'entrée (avec patient référence) :
echo {"criteres": [{"type": "meme", "cible": "portrait", "label": "Même portrait", "valeur": null, "reference_id": 2, "reference_patient": {"id": 2, "prenom": "Guillaume", "nom": "Moulin", "sexe": "M", "age": 19, "idportrait": "29"}}]}
echo.
python jsonsql.py "{\"criteres\": [{\"type\": \"meme\", \"cible\": \"portrait\", \"label\": \"Même portrait\", \"valeur\": null, \"reference_id\": 2, \"reference_patient\": {\"id\": 2, \"prenom\": \"Guillaume\", \"nom\": \"Moulin\", \"sexe\": \"M\", \"age\": 19, \"idportrait\": \"29\"}}]}" --debug
echo.
echo *** ATTENTION: Vérifier si "AND p.id != 2" apparaît dans le SQL ***
echo *** C'est le bug qui exclut Guillaume Moulin des résultats ***
echo.
pause

echo [TEST 5] trouve.py - Pipeline complet "%QUESTION_PORTRAIT%"
echo ----------------------------------------------------------------------
echo.
python trouve.py %BASE% "%QUESTION_PORTRAIT%" --verbose --debug
echo.
pause

echo [TEST 6] Vérifier manuellement le SQL généré
echo ----------------------------------------------------------------------
echo.
echo Requête attendue (SANS exclusion du patient référence):
echo SELECT DISTINCT p.id, p.prenom, p.nom, p.sexe, p.age, p.idportrait
echo FROM patients p
echo WHERE p.idportrait = '29'
echo ORDER BY p.id
echo.
echo Exécution directe:
sqlite3 %BASE% "SELECT id, prenom, nom, sexe, age, idportrait FROM patients WHERE idportrait = '29' ORDER BY id LIMIT 20;"
echo.
pause

echo [TEST 7] Combien de patients ont le même portrait (idportrait=29)?
echo ----------------------------------------------------------------------
echo.
sqlite3 %BASE% "SELECT COUNT(*) as nb FROM patients WHERE idportrait = '29';"
echo.
echo Liste complète:
sqlite3 %BASE% "SELECT id, prenom, nom, sexe, age FROM patients WHERE idportrait = '29' ORDER BY id;"
echo.
pause

echo ======================================================================
echo FIN DES TESTS
echo ======================================================================
