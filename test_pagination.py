# test_pagination.py V1.0.0 - 30/01/2026 13:48:48
#!/usr/bin/env python3
__pgm__ = "test_pagination.py"
__version__ = "1.0.0"
__date__ = "30/01/2026 13:48:48"

"""
Script de test pour la pagination optimisée /search/page.

Ce script teste :
1. La recherche initiale via /search (stocke en cache)
2. La pagination via /search/page (réutilise le cache)
3. Compare les temps de réponse

Usage:
    python test_pagination.py [URL_API] [BASE]
    
Exemples:
    python test_pagination.py
    python test_pagination.py http://localhost:8000 base25000.db
    python test_pagination.py https://kitview-search.onrender.com base100.db
"""

import requests
import json
import time
import uuid
import sys
from datetime import datetime


def print_header(title):
    """Affiche un en-tête formaté."""
    print()
    print("═" * 70)
    print(f"  {title}")
    print("═" * 70)


def print_result(label, value, indent=2):
    """Affiche un résultat formaté."""
    spaces = " " * indent
    print(f"{spaces}{label}: {value}")


def test_search_initial(api_url, question, base, session_id):
    """
    Test 1 : Recherche initiale via /search.
    Retourne le temps et le nombre de résultats.
    """
    print_header("TEST 1 : Recherche initiale /search")
    
    payload = {
        "question": question,
        "base": base,
        "lang": "auto",
        "mode_detection": "standard",
        "limit": 20,
        "offset": 0,
        "session_id": session_id
    }
    
    print(f"  Question: {question}")
    print(f"  Base: {base}")
    print(f"  Session ID: {session_id[:8]}...")
    print()
    
    start = time.perf_counter()
    
    try:
        response = requests.post(f"{api_url}/search", json=payload, timeout=30)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        if response.status_code != 200:
            print(f"  ❌ ERREUR HTTP {response.status_code}")
            print(f"  {response.text[:200]}")
            return None, None, elapsed_ms
        
        data = response.json()
        nb_total = data.get('nb_patients', 0)
        nb_retournes = len(data.get('patients', []))
        
        print(f"  ✓ Réponse reçue en {elapsed_ms:.0f}ms")
        print_result("Patients totaux", nb_total)
        print_result("Patients retournés", nb_retournes)
        print_result("Temps serveur", f"{data.get('temps_ms', 0)}ms")
        
        if nb_retournes > 0:
            p = data['patients'][0]
            print_result("Premier patient", f"{p.get('prenom', '')} {p.get('nom', '')} (ID {p.get('id', '?')})")
        
        return nb_total, nb_retournes, elapsed_ms
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ ERREUR: {e}")
        return None, None, 0


def test_search_page(api_url, session_id, offset, limit=20):
    """
    Test 2 : Pagination via /search/page.
    Retourne le temps et le nombre de résultats.
    """
    print_header(f"TEST 2 : Pagination /search/page (offset={offset})")
    
    payload = {
        "session_id": session_id,
        "offset": offset,
        "limit": limit
    }
    
    print(f"  Session ID: {session_id[:8]}...")
    print(f"  Offset: {offset}, Limit: {limit}")
    print()
    
    start = time.perf_counter()
    
    try:
        response = requests.post(f"{api_url}/search/page", json=payload, timeout=30)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        if response.status_code == 404:
            print(f"  ❌ Session non trouvée en cache (attendu si /search n'a pas été appelé)")
            return None, elapsed_ms
        
        if response.status_code != 200:
            print(f"  ❌ ERREUR HTTP {response.status_code}")
            print(f"  {response.text[:200]}")
            return None, elapsed_ms
        
        data = response.json()
        nb_retournes = len(data.get('patients', []))
        from_cache = data.get('from_cache', False)
        
        print(f"  ✓ Réponse reçue en {elapsed_ms:.0f}ms")
        print_result("Patients retournés", nb_retournes)
        print_result("Temps serveur", f"{data.get('temps_ms', 0)}ms")
        print_result("Depuis cache", "✓ Oui" if from_cache else "✗ Non")
        
        if nb_retournes > 0:
            p = data['patients'][0]
            print_result("Premier patient", f"{p.get('prenom', '')} {p.get('nom', '')} (ID {p.get('id', '?')})")
        
        return nb_retournes, elapsed_ms
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ ERREUR: {e}")
        return None, 0


def test_search_classic_pagination(api_url, question, base, offset, limit=20):
    """
    Test 3 : Pagination classique via /search (pour comparaison).
    Retourne le temps.
    """
    print_header(f"TEST 3 : Pagination classique /search (offset={offset})")
    
    payload = {
        "question": question,
        "base": base,
        "lang": "auto",
        "mode_detection": "standard",
        "limit": limit,
        "offset": offset,
        "session_id": str(uuid.uuid4())  # Nouvelle session
    }
    
    print(f"  Question: {question}")
    print(f"  Offset: {offset}, Limit: {limit}")
    print()
    
    start = time.perf_counter()
    
    try:
        response = requests.post(f"{api_url}/search", json=payload, timeout=30)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        if response.status_code != 200:
            print(f"  ❌ ERREUR HTTP {response.status_code}")
            return None
        
        data = response.json()
        nb_retournes = len(data.get('patients', []))
        
        print(f"  ✓ Réponse reçue en {elapsed_ms:.0f}ms")
        print_result("Patients retournés", nb_retournes)
        print_result("Temps serveur", f"{data.get('temps_ms', 0)}ms")
        
        return elapsed_ms
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ ERREUR: {e}")
        return None


def test_cache_stats(api_url):
    """Affiche les statistiques du cache."""
    print_header("STATISTIQUES CACHE")
    
    try:
        response = requests.get(f"{api_url}/search/cache/stats", timeout=10)
        
        if response.status_code != 200:
            print(f"  Endpoint non disponible (HTTP {response.status_code})")
            return
        
        data = response.json()
        print_result("Taille cache", data.get('cache_size', 0))
        print_result("Taille max", data.get('max_size', 0))
        print_result("TTL (minutes)", data.get('ttl_minutes', 0))
        
        sessions = data.get('sessions', [])
        if sessions:
            print()
            print("  Sessions en cache:")
            for s in sessions[:5]:
                print(f"    - {s['session_id']} : {s['question']} ({s['nb_total']} patients, {s['age_seconds']}s)")
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ ERREUR: {e}")


def main():
    """Point d'entrée principal."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Test de la pagination optimisée /search/page")
    print(f"╚════════════════════════════════════════════════════════════════")
    
    # Configuration
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    base = sys.argv[2] if len(sys.argv) > 2 else "base25000.db"
    question = "patients qui grincent des dents"
    session_id = str(uuid.uuid4())
    
    print()
    print(f"Configuration:")
    print(f"  API URL: {api_url}")
    print(f"  Base: {base}")
    print(f"  Question: {question}")
    
    # ═══════════════════════════════════════════════════════════════
    # TEST 1 : Recherche initiale
    # ═══════════════════════════════════════════════════════════════
    nb_total, nb_retournes, temps_initial = test_search_initial(
        api_url, question, base, session_id
    )
    
    if nb_total is None:
        print("\n❌ Test initial échoué, arrêt des tests.")
        return 1
    
    # ═══════════════════════════════════════════════════════════════
    # TEST 2 : Pagination optimisée (offset=20)
    # ═══════════════════════════════════════════════════════════════
    nb_page, temps_page = test_search_page(api_url, session_id, offset=20)
    
    # ═══════════════════════════════════════════════════════════════
    # TEST 3 : Pagination classique pour comparaison
    # ═══════════════════════════════════════════════════════════════
    temps_classic = test_search_classic_pagination(
        api_url, question, base, offset=20
    )
    
    # ═══════════════════════════════════════════════════════════════
    # TEST 4 : Pagination optimisée (offset=40)
    # ═══════════════════════════════════════════════════════════════
    nb_page2, temps_page2 = test_search_page(api_url, session_id, offset=40)
    
    # ═══════════════════════════════════════════════════════════════
    # STATISTIQUES CACHE
    # ═══════════════════════════════════════════════════════════════
    test_cache_stats(api_url)
    
    # ═══════════════════════════════════════════════════════════════
    # RÉSUMÉ COMPARATIF
    # ═══════════════════════════════════════════════════════════════
    print_header("RÉSUMÉ COMPARATIF")
    
    print(f"  Recherche initiale (/search)     : {temps_initial:.0f}ms")
    print(f"  Pagination optimisée (/search/page) : {temps_page:.0f}ms" if temps_page else "  Pagination optimisée : N/A")
    print(f"  Pagination classique (/search)   : {temps_classic:.0f}ms" if temps_classic else "  Pagination classique : N/A")
    
    if temps_page and temps_classic:
        gain = ((temps_classic - temps_page) / temps_classic) * 100
        facteur = temps_classic / temps_page if temps_page > 0 else 0
        print()
        print(f"  📊 GAIN DE PERFORMANCE:")
        print(f"     - Réduction: {gain:.1f}%")
        print(f"     - Facteur: {facteur:.1f}x plus rapide")
        
        if facteur >= 10:
            print(f"     ✓ Objectif atteint (>10x)")
        elif facteur >= 5:
            print(f"     ~ Bon résultat (5-10x)")
        else:
            print(f"     ⚠ Amélioration insuffisante (<5x)")
    
    print()
    print("═" * 70)
    print("  FIN DES TESTS")
    print("═" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
