# Prompt flipflop_architecture V1.0.0 - 15/12/2025 17:02:43

# Architecture Flip-Flop A/B pour KitviewSearch

## Concept

```
┌─────────────────────────────────────────────────────────────────┐
│                        RENDER                                    │
│  ┌─────────────┐              ┌─────────────┐                   │
│  │   Slot A    │              │   Slot B    │                   │
│  │  (v2.1.0)   │              │  (v2.0.1)   │                   │
│  └──────┬──────┘              └──────┬──────┘                   │
│         │                            │                          │
│         └────────────┬───────────────┘                          │
│                      │                                          │
│              ┌───────▼───────┐                                  │
│              │   Router      │  ← config.json : active = "A"    │
│              │  (main.py)    │                                  │
│              └───────┬───────┘                                  │
│                      │                                          │
└──────────────────────┼──────────────────────────────────────────┘
                       │
                       ▼
                   Utilisateurs
```

## Structure des fichiers

```
C:\KitviewSearchV201\
├── main.py              ← Point d'entrée, route vers A ou B
├── config.json          ← {"active": "A", "version_a": "2.1.0", "version_b": "2.0.1"}
├── slot_a/              ← Version A
│   ├── cherche.py
│   ├── suche.py
│   ├── traduire.py
│   ├── refs/
│   │   ├── pathoori.csv
│   │   └── pathosyn.csv
│   └── web/
│       └── index.html
├── slot_b/              ← Version B
│   ├── cherche.py
│   ├── suche.py
│   └── ...
└── admin/
    └── admin.html       ← Interface admin (roue dentée)
```

## Fichier config.json

```json
{
    "active": "A",
    "version_a": "2.1.0",
    "version_b": "2.0.1",
    "last_switch": "2025-12-15T14:30:00",
    "switch_history": [
        {"from": "B", "to": "A", "date": "2025-12-15T14:30:00", "reason": "Mise à jour japonais"}
    ]
}
```

## main.py - Routeur principal

```python
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
import json
import os
import sys

app = FastAPI()

CONFIG_FILE = "config.json"

def get_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def get_active_slot():
    config = get_config()
    return config.get("active", "A").upper()

# Ajouter le slot actif au path Python
slot = get_active_slot()
sys.path.insert(0, f"slot_{slot.lower()}")

# Import dynamique du module de recherche
if slot == "A":
    from slot_a.suche import sucher
    from slot_a import cherche
else:
    from slot_b.suche import sucher
    from slot_b import cherche

# === API ADMIN ===

@app.get("/api/admin/status")
async def admin_status():
    """Retourne le statut actuel (slot actif, versions)"""
    config = get_config()
    return {
        "active": config["active"],
        "version_a": config.get("version_a", "?"),
        "version_b": config.get("version_b", "?"),
        "last_switch": config.get("last_switch")
    }

@app.post("/api/admin/switch")
async def admin_switch(request: Request):
    """Bascule vers l'autre slot"""
    data = await request.json()
    password = data.get("password", "")
    
    # Vérification mot de passe simple
    if password != os.environ.get("ADMIN_PASSWORD", "kitview2025"):
        return JSONResponse({"error": "Mot de passe incorrect"}, status_code=403)
    
    config = get_config()
    old_slot = config["active"]
    new_slot = "B" if old_slot == "A" else "A"
    
    config["active"] = new_slot
    config["last_switch"] = datetime.now().isoformat()
    config["switch_history"].append({
        "from": old_slot,
        "to": new_slot,
        "date": config["last_switch"],
        "reason": data.get("reason", "Manuel")
    })
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    return {"success": True, "active": new_slot, "message": f"Basculé de {old_slot} vers {new_slot}"}

# === ROUTES PRINCIPALES ===

@app.get("/")
async def home():
    slot = get_active_slot()
    return RedirectResponse(f"/slot_{slot.lower()}/web/index.html")

@app.get("/api/search")
async def search(q: str, lang: str = "auto", ...):
    # Utilise le module du slot actif
    return sucher(question=q, lang=lang, ...)
```

## Interface Admin (roue dentée)

Dans `index.html`, ajouter un bouton roue dentée qui ouvre une modal :

```html
<!-- Bouton roue dentée (admin) -->
<button id="adminBtn" onclick="openAdmin()" title="Administration">⚙️</button>

<!-- Modal Admin -->
<div id="adminModal" class="modal">
    <div class="modal-content">
        <h2>⚙️ Administration</h2>
        
        <div class="status-box">
            <p><strong>Slot actif :</strong> <span id="activeSlot">A</span></p>
            <p><strong>Version A :</strong> <span id="versionA">2.1.0</span></p>
            <p><strong>Version B :</strong> <span id="versionB">2.0.1</span></p>
        </div>
        
        <div class="switch-box">
            <label>Mot de passe :</label>
            <input type="password" id="adminPassword">
            
            <label>Raison (optionnel) :</label>
            <input type="text" id="switchReason" placeholder="Ex: Rollback bug...">
            
            <button onclick="switchSlot()">🔄 Basculer vers l'autre slot</button>
        </div>
        
        <button onclick="closeAdmin()">Fermer</button>
    </div>
</div>

<script>
async function loadAdminStatus() {
    const resp = await fetch('/api/admin/status');
    const data = await resp.json();
    document.getElementById('activeSlot').textContent = data.active;
    document.getElementById('versionA').textContent = data.version_a;
    document.getElementById('versionB').textContent = data.version_b;
}

async function switchSlot() {
    const password = document.getElementById('adminPassword').value;
    const reason = document.getElementById('switchReason').value;
    
    const resp = await fetch('/api/admin/switch', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({password, reason})
    });
    
    const data = await resp.json();
    if (data.success) {
        alert(`✅ ${data.message}\nRechargez la page.`);
        location.reload();
    } else {
        alert(`❌ Erreur : ${data.error}`);
    }
}
</script>
```

## Workflow de mise à jour

### Mise à jour normale (flip-flop)

```bash
# 1. Vérifier quel slot est actif
curl https://kitviewsearch.onrender.com/api/admin/status
# → {"active": "A", ...}

# 2. Mettre à jour le slot INACTIF (B)
# Le script update_render.cmd copie vers slot_b/

# 3. Tester sur l'URL de test
# https://kitviewsearch.onrender.com/slot_b/web/index.html

# 4. Si OK, basculer via l'interface admin (roue dentée)
# Ou via API :
curl -X POST https://kitviewsearch.onrender.com/api/admin/switch \
     -H "Content-Type: application/json" \
     -d '{"password":"kitview2025","reason":"Mise à jour v2.1.0"}'
```

### Rollback d'urgence

1. Cliquer sur ⚙️ (roue dentée)
2. Entrer le mot de passe
3. Cliquer "Basculer vers l'autre slot"
4. La version précédente est immédiatement active

## Avantages

| Avantage | Description |
|----------|-------------|
| **Zero downtime** | La bascule est instantanée (changement de config) |
| **Rollback immédiat** | Un clic pour revenir à la version précédente |
| **Test en prod** | Possibilité de tester slot_b avant de basculer |
| **Historique** | Traçabilité des bascules dans config.json |
| **Sécurisé** | Mot de passe requis pour basculer |

## Script de déploiement flip-flop

```cmd
@echo off
REM deploy_flipflop.cmd - Déploie vers le slot inactif

REM 1. Récupérer le slot actif
curl -s https://kitviewsearch.onrender.com/api/admin/status > status.json
for /f "tokens=2 delims=:," %%a in ('type status.json ^| findstr "active"') do set ACTIVE=%%~a
set ACTIVE=%ACTIVE: =%
set ACTIVE=%ACTIVE:"=%

REM 2. Déterminer le slot cible (l'autre)
if "%ACTIVE%"=="A" (
    set TARGET=B
) else (
    set TARGET=A
)

echo Slot actif : %ACTIVE%
echo Slot cible : %TARGET%

REM 3. Copier vers le slot cible
set DEST=C:\KitviewSearchV201\slot_%TARGET%
xcopy "D:\KitviewSearchV210\*" "%DEST%\" /E /I /H /Y

REM 4. Git commit et push
cd C:\KitviewSearchV201
git add -A
git commit -m "Update slot_%TARGET% to v2.1.0"
git push

echo.
echo ✓ Slot %TARGET% mis à jour. Testez puis basculez via l'admin.
```

## Prochaines étapes

1. **Phase 1** : Mise à jour simple (script `update_render.cmd`)
2. **Phase 2** : Restructurer en slots A/B
3. **Phase 3** : Ajouter l'interface admin
4. **Phase 4** : Script de déploiement flip-flop automatique
