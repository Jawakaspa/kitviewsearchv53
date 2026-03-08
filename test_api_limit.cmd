@echo off
REM Test API /search - Vérifier le comportement de limit
REM Exécuter depuis le répertoire du projet

echo === TEST 1 : Requete avec limit=20 ===
curl -X POST http://localhost:8000/search -H "Content-Type: application/json" -d "{\"question\": \"qui grincent des dents\", \"base\": \"base25000.db\", \"mode\": \"sc\", \"limit\": 20, \"offset\": 0}" 2>nul | python -c "import sys,json; d=json.load(sys.stdin); print(f'nb_patients: {d.get(\"nb_patients\",\"?\")}'); print(f'patients retournes: {len(d.get(\"patients\",[]))}')"

echo.
echo === TEST 2 : Requete avec limit=100 ===
curl -X POST http://localhost:8000/search -H "Content-Type: application/json" -d "{\"question\": \"qui grincent des dents\", \"base\": \"base25000.db\", \"mode\": \"sc\", \"limit\": 100, \"offset\": 0}" 2>nul | python -c "import sys,json; d=json.load(sys.stdin); print(f'nb_patients: {d.get(\"nb_patients\",\"?\")}'); print(f'patients retournes: {len(d.get(\"patients\",[]))}')"

echo.
echo === TEST 3 : Requete avec limit=100, offset=100 ===
curl -X POST http://localhost:8000/search -H "Content-Type: application/json" -d "{\"question\": \"qui grincent des dents\", \"base\": \"base25000.db\", \"mode\": \"sc\", \"limit\": 100, \"offset\": 100}" 2>nul | python -c "import sys,json; d=json.load(sys.stdin); print(f'nb_patients: {d.get(\"nb_patients\",\"?\")}'); print(f'patients retournes: {len(d.get(\"patients\",[]))}')"

echo.
echo === RESULTATS ATTENDUS ===
echo TEST 1 : patients retournes = 20 (pas plus)
echo TEST 2 : patients retournes = 100 (pas plus)
echo TEST 3 : patients retournes = 100 (pas plus)
echo.
echo Si le serveur retourne TOUS les patients, le bug est cote serveur.
echo Si le serveur retourne bien limit patients, le bug est cote frontend.
pause
