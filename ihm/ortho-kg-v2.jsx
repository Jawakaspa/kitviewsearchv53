import { useState, useEffect, useRef, useCallback, useMemo } from "react";

const CAT_META = {
  pathologie:   { color: "#ef4444", border: "#dc2626", icon: "🔴", label: "Pathologies (71)" },
  traitement:   { color: "#10b981", border: "#059669", icon: "🟢", label: "Traitements (31)" },
  biomécanique: { color: "#8b5cf6", border: "#7c3aed", icon: "🟣", label: "Biomécanique (13)" },
  fonction:     { color: "#f59e0b", border: "#d97706", icon: "🟡", label: "Fonctions (12)" },
  diagnostic:   { color: "#3b82f6", border: "#2563eb", icon: "🔵", label: "Diagnostic (9)" },
  anatomie:     { color: "#ec4899", border: "#db2777", icon: "🩷", label: "Anatomie (8)" },
  matériau:     { color: "#6b7280", border: "#4b5563", icon: "⚪", label: "Matériaux (4)" },
  gestion:      { color: "#78716c", border: "#57534e", icon: "⬜", label: "Gestion (3)" },
};

// All 151 tags from V2, with category
const ALL_TAGS = [
  // PATHOLOGIE (71)
  {id:"malocclusion",cat:"pathologie",sub:"classification"},{id:"classe i d'angle",cat:"pathologie",sub:"classification"},
  {id:"classe ii d'angle",cat:"pathologie",sub:"classification"},{id:"classe iii d'angle",cat:"pathologie",sub:"classification"},
  {id:"classe i squelettique",cat:"pathologie",sub:"classification"},{id:"classe ii squelettique",cat:"pathologie",sub:"classification"},
  {id:"classe iii squelettique",cat:"pathologie",sub:"classification"},
  {id:"béance",cat:"pathologie",sub:"occlusion"},{id:"supraclusion",cat:"pathologie",sub:"occlusion"},
  {id:"occlusion croisée",cat:"pathologie",sub:"occlusion"},{id:"occlusion inversée",cat:"pathologie",sub:"occlusion"},
  {id:"overjet",cat:"pathologie",sub:"occlusion"},{id:"endoalvéolie",cat:"pathologie",sub:"occlusion"},
  {id:"crowding",cat:"pathologie",sub:"position"},{id:"ddm",cat:"pathologie",sub:"position"},
  {id:"diastème",cat:"pathologie",sub:"position"},{id:"diastemata",cat:"pathologie",sub:"position"},
  {id:"malposition",cat:"pathologie",sub:"position"},{id:"ectopie",cat:"pathologie",sub:"position"},
  {id:"protrusion",cat:"pathologie",sub:"position"},{id:"bipro",cat:"pathologie",sub:"position"},
  {id:"proglissement",cat:"pathologie",sub:"position"},{id:"latérodéviation",cat:"pathologie",sub:"position"},
  {id:"déviation mandibulaire",cat:"pathologie",sub:"position"},{id:"déviation maxillaire",cat:"pathologie",sub:"position"},
  {id:"prognathie mandibulaire",cat:"pathologie",sub:"squelettique"},{id:"prognathisme maxillaire",cat:"pathologie",sub:"squelettique"},
  {id:"rétrognathie mandibulaire",cat:"pathologie",sub:"squelettique"},{id:"rétrognathie maxillaire",cat:"pathologie",sub:"squelettique"},
  {id:"macrognathie",cat:"pathologie",sub:"squelettique"},{id:"micrognathie",cat:"pathologie",sub:"squelettique"},
  {id:"asymétrie faciale",cat:"pathologie",sub:"squelettique"},{id:"wits",cat:"pathologie",sub:"squelettique"},
  {id:"rétroalvéolie",cat:"pathologie",sub:"alvéolaire"},{id:"procheilie",cat:"pathologie",sub:"alvéolaire"},
  {id:"rétrocheilie",cat:"pathologie",sub:"alvéolaire"},
  {id:"agénésie",cat:"pathologie",sub:"dentaire"},{id:"dent surnuméraire",cat:"pathologie",sub:"dentaire"},
  {id:"inclusion",cat:"pathologie",sub:"dentaire"},{id:"macrodontie",cat:"pathologie",sub:"dentaire"},
  {id:"microdontie",cat:"pathologie",sub:"dentaire"},{id:"éruption ectopique",cat:"pathologie",sub:"dentaire"},
  {id:"ankylose",cat:"pathologie",sub:"dentaire"},{id:"édentation",cat:"pathologie",sub:"dentaire"},
  {id:"interposition linguale",cat:"pathologie",sub:"fonctionnel"},
  {id:"dysfonction linguale",cat:"pathologie",sub:"fonctionnel"},{id:"respiration buccale",cat:"pathologie",sub:"fonctionnel"},
  {id:"onychophagie",cat:"pathologie",sub:"fonctionnel"},{id:"bruxisme",cat:"pathologie",sub:"fonctionnel"},
  {id:"apnée du sommeil",cat:"pathologie",sub:"fonctionnel"},
  {id:"atm",cat:"pathologie",sub:"atm"},{id:"dtm",cat:"pathologie",sub:"atm"},
  {id:"claquement articulaire",cat:"pathologie",sub:"atm"},{id:"ressaut articulaire",cat:"pathologie",sub:"atm"},
  {id:"luxation",cat:"pathologie",sub:"atm"},{id:"luxation méniscale",cat:"pathologie",sub:"atm"},
  {id:"arthrite",cat:"pathologie",sub:"atm"},{id:"arthrose",cat:"pathologie",sub:"atm"},
  {id:"caries dentaires",cat:"pathologie",sub:"paro"},{id:"maladie parodontale",cat:"pathologie",sub:"paro"},
  {id:"gingivite",cat:"pathologie",sub:"paro"},{id:"récession gingivale",cat:"pathologie",sub:"paro"},
  {id:"résorption radiculaire",cat:"pathologie",sub:"paro"},{id:"nécrose pulpaire",cat:"pathologie",sub:"paro"},
  {id:"érosion",cat:"pathologie",sub:"paro"},{id:"fluorose",cat:"pathologie",sub:"paro"},
  {id:"fente",cat:"pathologie",sub:"autre"},{id:"dysplasie",cat:"pathologie",sub:"autre"},
  {id:"fracture",cat:"pathologie",sub:"autre"},{id:"douleur",cat:"pathologie",sub:"autre"},
  {id:"récidive",cat:"pathologie",sub:"autre"},{id:"diabète",cat:"pathologie",sub:"autre"},
  // TRAITEMENT (31)
  {id:"bagues",cat:"traitement",sub:"fixe"},{id:"gouttière",cat:"traitement",sub:"fixe"},
  {id:"orthodontie linguale",cat:"traitement",sub:"fixe"},{id:"contention",cat:"traitement",sub:"fixe"},
  {id:"activateur",cat:"traitement",sub:"amovible"},{id:"plaque amovible",cat:"traitement",sub:"amovible"},
  {id:"plaque éventail",cat:"traitement",sub:"amovible"},{id:"plaque papillon",cat:"traitement",sub:"amovible"},
  {id:"plaque y",cat:"traitement",sub:"amovible"},{id:"propulsor",cat:"traitement",sub:"amovible"},
  {id:"quad helix",cat:"traitement",sub:"dispositif"},{id:"bielles",cat:"traitement",sub:"dispositif"},
  {id:"pendulum",cat:"traitement",sub:"dispositif"},{id:"écarteur",cat:"traitement",sub:"dispositif"},
  {id:"arc transpalatin",cat:"traitement",sub:"dispositif"},{id:"auxiliaire",cat:"traitement",sub:"dispositif"},
  {id:"minivis",cat:"traitement",sub:"dispositif"},{id:"élastiques intermaxillaires",cat:"traitement",sub:"dispositif"},
  {id:"ancrage",cat:"traitement",sub:"dispositif"},
  {id:"chirurgie",cat:"traitement",sub:"intervention"},{id:"ostéotomie",cat:"traitement",sub:"intervention"},
  {id:"avulsion",cat:"traitement",sub:"intervention"},{id:"stripping",cat:"traitement",sub:"intervention"},
  {id:"détartrage",cat:"traitement",sub:"intervention"},{id:"implant",cat:"traitement",sub:"intervention"},
  {id:"facette",cat:"traitement",sub:"intervention"},
  {id:"distalisation",cat:"traitement",sub:"mouvement"},{id:"mésialisation",cat:"traitement",sub:"mouvement"},
  {id:"traitement interceptif",cat:"traitement",sub:"autre"},{id:"débandage",cat:"traitement",sub:"autre"},
  {id:"mainteneur d'espace",cat:"traitement",sub:"autre"},
  // BIOMÉCANIQUE (13)
  {id:"alignement",cat:"biomécanique",sub:""},{id:"arc orthodontique",cat:"biomécanique",sub:""},
  {id:"égression",cat:"biomécanique",sub:""},{id:"ingression",cat:"biomécanique",sub:""},
  {id:"rotation",cat:"biomécanique",sub:""},{id:"torque",cat:"biomécanique",sub:""},
  {id:"translation",cat:"biomécanique",sub:""},{id:"transposition",cat:"biomécanique",sub:""},
  {id:"version",cat:"biomécanique",sub:""},{id:"vestibulo-version",cat:"biomécanique",sub:""},
  {id:"linguo-version",cat:"biomécanique",sub:""},{id:"force orthodontique",cat:"biomécanique",sub:""},
  {id:"nivellement",cat:"biomécanique",sub:""},
  // FONCTION (12)
  {id:"déglutition",cat:"fonction",sub:""},{id:"mastication",cat:"fonction",sub:""},
  {id:"phonation",cat:"fonction",sub:""},{id:"ventilation nasale",cat:"fonction",sub:""},
  {id:"aéro",cat:"fonction",sub:""},{id:"succion",cat:"fonction",sub:""},
  {id:"croissance",cat:"fonction",sub:""},{id:"éruption",cat:"fonction",sub:""},
  {id:"dentition mixte",cat:"fonction",sub:""},{id:"dentition permanente",cat:"fonction",sub:""},
  {id:"dentition temporaire",cat:"fonction",sub:""},{id:"engrènement",cat:"fonction",sub:""},
  // DIAGNOSTIC (9)
  {id:"céphalométrie",cat:"diagnostic",sub:""},{id:"panoramique",cat:"diagnostic",sub:""},
  {id:"scanner",cat:"diagnostic",sub:""},{id:"scanner intra-oral",cat:"diagnostic",sub:""},
  {id:"empreinte",cat:"diagnostic",sub:""},{id:"consultation",cat:"diagnostic",sub:""},
  {id:"contrôle",cat:"diagnostic",sub:""},{id:"analyse de bolton",cat:"diagnostic",sub:""},
  {id:"photographie clinique",cat:"diagnostic",sub:""},
  // ANATOMIE (8)
  {id:"canine",cat:"anatomie",sub:""},{id:"molaire",cat:"anatomie",sub:""},
  {id:"prémolaire",cat:"anatomie",sub:""},{id:"incisives latérales",cat:"anatomie",sub:""},
  {id:"incisives palatinées",cat:"anatomie",sub:""},{id:"mandibule normopositionnée",cat:"anatomie",sub:""},
  {id:"maxillaire normopositionné",cat:"anatomie",sub:""},
  {id:"atm_anat",cat:"anatomie",sub:"",label:"ATM (anatomie)"},
  // MATÉRIAU (4)
  {id:"métal",cat:"matériau",sub:""},{id:"céramique",cat:"matériau",sub:""},
  {id:"niti",cat:"matériau",sub:""},{id:"composite",cat:"matériau",sub:""},
  // GESTION (3)
  {id:"urgence",cat:"gestion",sub:""},{id:"favori",cat:"gestion",sub:""},{id:"ef",cat:"gestion",sub:""},
];

// Clinical relationships (edges)
const EDGES = [
  // Classification → sous-types
  {s:"malocclusion",t:"classe i d'angle",l:"type"},{s:"malocclusion",t:"classe ii d'angle",l:"type"},
  {s:"malocclusion",t:"classe iii d'angle",l:"type"},{s:"malocclusion",t:"béance",l:"inclut"},
  {s:"malocclusion",t:"supraclusion",l:"inclut"},{s:"malocclusion",t:"occlusion croisée",l:"inclut"},
  {s:"malocclusion",t:"occlusion inversée",l:"inclut"},{s:"malocclusion",t:"overjet",l:"inclut"},
  {s:"malocclusion",t:"endoalvéolie",l:"inclut"},
  // Classes squelettiques
  {s:"classe ii d'angle",t:"classe ii squelettique",l:"composante"},{s:"classe iii d'angle",t:"classe iii squelettique",l:"composante"},
  {s:"classe i d'angle",t:"classe i squelettique",l:"composante"},
  // Squelettique
  {s:"classe ii squelettique",t:"rétrognathie mandibulaire",l:"souvent"},{s:"classe ii squelettique",t:"prognathisme maxillaire",l:"parfois"},
  {s:"classe iii squelettique",t:"prognathie mandibulaire",l:"souvent"},{s:"classe iii squelettique",t:"rétrognathie maxillaire",l:"parfois"},
  {s:"wits",t:"classe ii squelettique",l:"mesure"},{s:"wits",t:"classe iii squelettique",l:"mesure"},
  {s:"asymétrie faciale",t:"latérodéviation",l:"liée à"},{s:"asymétrie faciale",t:"déviation mandibulaire",l:"liée à"},
  // Traitements ← Pathologies
  {s:"classe ii d'angle",t:"bielles",l:"traité par"},{s:"classe ii d'angle",t:"activateur",l:"traité par"},
  {s:"classe ii d'angle",t:"propulsor",l:"traité par"},{s:"classe ii d'angle",t:"élastiques intermaxillaires",l:"traité par"},
  {s:"classe iii d'angle",t:"chirurgie",l:"peut nécessiter"},{s:"classe iii d'angle",t:"ostéotomie",l:"peut nécessiter"},
  {s:"crowding",t:"stripping",l:"traité par"},{s:"crowding",t:"avulsion",l:"traité par"},
  {s:"crowding",t:"bagues",l:"traité par"},{s:"crowding",t:"gouttière",l:"traité par"},
  {s:"endoalvéolie",t:"quad helix",l:"traité par"},{s:"endoalvéolie",t:"écarteur",l:"traité par"},
  {s:"béance",t:"dysfonction linguale",l:"causée par"},{s:"béance",t:"interposition linguale",l:"causée par"},
  {s:"béance",t:"succion",l:"causée par"},
  {s:"supraclusion",t:"ingression",l:"corrigée par"},{s:"overjet",t:"égression",l:"corrigée par"},
  {s:"inclusion",t:"chirurgie",l:"peut nécessiter"},{s:"inclusion",t:"avulsion",l:"ou"},
  {s:"récidive",t:"contention",l:"prévenue par"},
  // Biomécanique → Traitements
  {s:"bagues",t:"arc orthodontique",l:"utilise"},{s:"bagues",t:"auxiliaire",l:"utilise"},
  {s:"bagues",t:"élastiques intermaxillaires",l:"utilise"},{s:"minivis",t:"ancrage",l:"fournit"},
  {s:"force orthodontique",t:"résorption radiculaire",l:"risque"},{s:"force orthodontique",t:"translation",l:"produit"},
  {s:"distalisation",t:"pendulum",l:"par"},{s:"distalisation",t:"minivis",l:"par"},
  // Diagnostic
  {s:"céphalométrie",t:"classe ii squelettique",l:"identifie"},{s:"céphalométrie",t:"classe iii squelettique",l:"identifie"},
  {s:"céphalométrie",t:"wits",l:"mesure"},{s:"panoramique",t:"agénésie",l:"détecte"},
  {s:"panoramique",t:"inclusion",l:"détecte"},{s:"panoramique",t:"dent surnuméraire",l:"détecte"},
  {s:"scanner",t:"inclusion",l:"localise"},{s:"analyse de bolton",t:"ddm",l:"quantifie"},
  {s:"scanner intra-oral",t:"empreinte",l:"remplace"},
  // Fonctions
  {s:"dysfonction linguale",t:"déglutition",l:"perturbe"},{s:"respiration buccale",t:"ventilation nasale",l:"oppose"},
  {s:"respiration buccale",t:"béance",l:"favorise"},{s:"bruxisme",t:"atm",l:"affecte"},
  {s:"croissance",t:"traitement interceptif",l:"fenêtre"},
  // ATM
  {s:"dtm",t:"claquement articulaire",l:"symptôme"},{s:"dtm",t:"luxation méniscale",l:"symptôme"},
  {s:"dtm",t:"arthrose",l:"évolution"},{s:"dtm",t:"douleur",l:"symptôme"},
  {s:"atm",t:"dtm",l:"siège de"},
  // Matériaux → Traitements
  {s:"métal",t:"bagues",l:"composant"},{s:"céramique",t:"gouttière",l:"alternative"},
  {s:"niti",t:"arc orthodontique",l:"composant"},
  // Parodontie
  {s:"maladie parodontale",t:"récession gingivale",l:"inclut"},{s:"gingivite",t:"maladie parodontale",l:"évolue vers"},
];

// Layout: radial by category
const CX = 700, CY = 450;
const catAngles = {
  pathologie: { start: -30, end: 150, r: [120, 380] },
  traitement: { start: 155, end: 260, r: [120, 360] },
  biomécanique: { start: 265, end: 310, r: [140, 340] },
  fonction: { start: -85, end: -35, r: [140, 340] },
  diagnostic: { start: 312, end: 345, r: [160, 330] },
  anatomie: { start: -120, end: -88, r: [160, 300] },
  matériau: { start: 347, end: 365, r: [170, 290] },
  gestion: { start: -145, end: -125, r: [180, 280] },
};

function layoutNodes() {
  const nodes = [];
  const catGroups = {};
  ALL_TAGS.forEach(t => {
    if (!catGroups[t.cat]) catGroups[t.cat] = [];
    catGroups[t.cat].push(t);
  });

  Object.entries(catGroups).forEach(([cat, items]) => {
    const cfg = catAngles[cat];
    if (!cfg) return;
    const n = items.length;
    items.forEach((item, i) => {
      const angleDeg = cfg.start + (cfg.end - cfg.start) * (i / Math.max(n - 1, 1));
      const angleRad = (angleDeg * Math.PI) / 180;
      const layers = n > 15 ? 3 : n > 8 ? 2 : 1;
      const layer = layers > 1 ? (i % layers) : 0;
      const rMin = cfg.r[0];
      const rMax = cfg.r[1];
      const r = rMin + ((rMax - rMin) * (layer + 0.5)) / layers;
      nodes.push({
        ...item,
        label: item.label || item.id,
        x: CX + r * Math.cos(angleRad),
        y: CY + r * Math.sin(angleRad),
      });
    });
  });

  // Add central node
  nodes.push({ id: "orthodontie", cat: "core", sub: "", label: "Orthodontie", x: CX, y: CY });
  return nodes;
}

export default function OrthoKGv2() {
  const [nodes] = useState(() => layoutNodes());
  const [hovered, setHovered] = useState(null);
  const [selected, setSelected] = useState(null);
  const [filterCat, setFilterCat] = useState(null);
  const [search, setSearch] = useState("");
  const svgRef = useRef(null);

  const nodeMap = useMemo(() => {
    const m = {};
    nodes.forEach(n => m[n.id] = n);
    return m;
  }, [nodes]);

  const activeId = selected || hovered;

  const connectedIds = useMemo(() => {
    if (!activeId) return new Set();
    const s = new Set([activeId]);
    EDGES.forEach(e => {
      if (e.s === activeId) s.add(e.t);
      if (e.t === activeId) s.add(e.s);
    });
    return s;
  }, [activeId]);

  const activeEdges = useMemo(() => {
    if (!activeId) return [];
    return EDGES.filter(e => e.s === activeId || e.t === activeId);
  }, [activeId]);

  const searchLower = search.toLowerCase();
  const matchesSearch = useCallback((n) => {
    if (!searchLower) return true;
    return n.label.toLowerCase().includes(searchLower) || n.id.toLowerCase().includes(searchLower);
  }, [searchLower]);

  const isVisible = useCallback((n) => {
    if (n.id === "orthodontie") return true;
    if (filterCat && n.cat !== filterCat) return false;
    if (searchLower && !matchesSearch(n)) return false;
    return true;
  }, [filterCat, searchLower, matchesSearch]);

  const getOpacity = useCallback((n) => {
    if (!isVisible(n)) return 0.04;
    if (activeId && !connectedIds.has(n.id)) return 0.12;
    return 1;
  }, [isVisible, activeId, connectedIds]);

  const visibleCount = nodes.filter(n => isVisible(n) && n.id !== "orthodontie").length;

  return (
    <div style={{ background: "#0a0a0f", minHeight: "100vh", fontFamily: "'Segoe UI',system-ui,sans-serif", color: "#e2e8f0", padding: "12px" }}>
      <div style={{ textAlign: "center", marginBottom: 8 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 4px", color: "#f1f5f9" }}>
          🦷 Knowledge Graph Orthodontie — V2 Complète
        </h1>
        <p style={{ fontSize: 12, color: "#94a3b8", margin: 0 }}>
          {visibleCount} tags affichés · Survolez pour explorer · Cliquez pour verrouiller
        </p>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, justifyContent: "center", marginBottom: 8, alignItems: "center" }}>
        <input
          type="text" placeholder="🔍 Rechercher un tag…" value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ padding: "4px 10px", borderRadius: 6, border: "1px solid #334155", background: "#1e293b", color: "#e2e8f0", fontSize: 12, width: 180 }}
        />
        <button
          onClick={() => { setFilterCat(null); setSelected(null); }}
          style={{ padding: "3px 10px", borderRadius: 6, border: filterCat === null ? "2px solid #c084fc" : "1px solid #475569", background: filterCat === null ? "#1e1b4b" : "#1e293b", color: "#e2e8f0", fontSize: 11, cursor: "pointer" }}
        >Tout</button>
        {Object.entries(CAT_META).map(([key, meta]) => (
          <button key={key}
            onClick={() => { setFilterCat(filterCat === key ? null : key); setSelected(null); }}
            style={{ padding: "3px 10px", borderRadius: 6, border: filterCat === key ? `2px solid ${meta.color}` : "1px solid #475569", background: filterCat === key ? meta.color + "22" : "#1e293b", color: meta.color, fontSize: 11, cursor: "pointer" }}
          >{meta.icon} {key}</button>
        ))}
      </div>

      <svg ref={svgRef} viewBox="0 0 1400 900" style={{ width: "100%", maxHeight: "72vh", borderRadius: 12, border: "1px solid #1e293b", background: "#0f172a" }}>
        <defs>
          <marker id="ah" markerWidth="6" markerHeight="5" refX="6" refY="2.5" orient="auto">
            <polygon points="0 0,6 2.5,0 5" fill="#475569" />
          </marker>
          <marker id="ah-a" markerWidth="6" markerHeight="5" refX="6" refY="2.5" orient="auto">
            <polygon points="0 0,6 2.5,0 5" fill="#a78bfa" />
          </marker>
          <filter id="gl"><feGaussianBlur stdDeviation="4" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        </defs>

        {/* All edges (background) */}
        {EDGES.map((e, i) => {
          const sn = nodeMap[e.s], tn = nodeMap[e.t];
          if (!sn || !tn) return null;
          const isActive = activeId && (e.s === activeId || e.t === activeId);
          const bothVisible = isVisible(sn) && isVisible(tn);
          if (!bothVisible && !isActive) return null;
          return (
            <line key={`e${i}`} x1={sn.x} y1={sn.y} x2={tn.x} y2={tn.y}
              stroke={isActive ? "#a78bfa" : "#334155"} strokeWidth={isActive ? 1.5 : 0.4}
              opacity={isActive ? 1 : (activeId ? 0.05 : 0.15)}
              markerEnd={isActive ? "url(#ah-a)" : "url(#ah)"}
            />
          );
        })}

        {/* Edge labels when active */}
        {activeEdges.map((e, i) => {
          const sn = nodeMap[e.s], tn = nodeMap[e.t];
          if (!sn || !tn) return null;
          return (
            <text key={`el${i}`} x={(sn.x + tn.x) / 2} y={(sn.y + tn.y) / 2 - 5}
              textAnchor="middle" fill="#c4b5fd" fontSize="7" fontStyle="italic">{e.l}</text>
          );
        })}

        {/* Nodes */}
        {nodes.map(n => {
          const meta = n.cat === "core" ? { color: "#6366f1", border: "#4f46e5" } : CAT_META[n.cat] || { color: "#666", border: "#555" };
          const isCore = n.id === "orthodontie";
          const isActive = activeId === n.id;
          const op = isCore ? 1 : getOpacity(n);
          const r = isCore ? 30 : (n.label.length > 18 ? 22 : 18);
          const label = n.label.length > 22 ? n.label.slice(0, 20) + "…" : n.label;

          return (
            <g key={n.id} opacity={op} style={{ cursor: "pointer", transition: "opacity 0.2s" }}
              onMouseEnter={() => setHovered(n.id)} onMouseLeave={() => setHovered(null)}
              onClick={() => setSelected(s => s === n.id ? null : n.id)}>
              {isActive && <circle cx={n.x} cy={n.y} r={r + 5} fill="none" stroke="#a78bfa" strokeWidth={2} filter="url(#gl)" />}
              <circle cx={n.x} cy={n.y} r={r} fill={meta.color} stroke={meta.border} strokeWidth={1.5} />
              <text x={n.x} y={n.y + 0.5} textAnchor="middle" dominantBaseline="central"
                fill="#fff" fontSize={isCore ? 11 : 7} fontWeight={isCore ? 700 : 500}>
                {label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Info panel */}
      {selected && nodeMap[selected] && (
        <div style={{ marginTop: 10, background: "#1e293b", border: "1px solid #334155", borderRadius: 10, padding: 14, maxWidth: 500, marginLeft: "auto", marginRight: "auto" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <div style={{ width: 12, height: 12, borderRadius: "50%", background: (CAT_META[nodeMap[selected].cat] || {}).color || "#6366f1" }} />
            <strong style={{ fontSize: 15 }}>{nodeMap[selected].label}</strong>
            <span style={{ fontSize: 11, color: "#94a3b8", marginLeft: "auto" }}>{nodeMap[selected].cat} {nodeMap[selected].sub ? `· ${nodeMap[selected].sub}` : ""}</span>
          </div>
          <div style={{ fontSize: 13 }}>
            {activeEdges.length === 0 && <span style={{ color: "#64748b" }}>Aucune relation définie</span>}
            {activeEdges.map((e, i) => {
              const isSource = e.s === selected;
              const otherId = isSource ? e.t : e.s;
              const other = nodeMap[otherId];
              if (!other) return null;
              return (
                <div key={i} style={{ padding: "2px 0", display: "flex", gap: 6, alignItems: "center" }}>
                  <span style={{ color: "#64748b" }}>{isSource ? "→" : "←"}</span>
                  <span style={{ color: "#c4b5fd", fontStyle: "italic", fontSize: 11 }}>{e.l}</span>
                  <span>{other.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
