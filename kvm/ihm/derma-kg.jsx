import { useState, useMemo, useRef, useCallback } from "react";

const CAT_META = {
  core:         { color: "#6366f1", border: "#4f46e5", label: "Dermatologie" },
  inflammatoire:{ color: "#ef4444", border: "#dc2626", label: "Inflammatoire" },
  infectieux:   { color: "#f97316", border: "#ea580c", label: "Infectieux" },
  tumoral:      { color: "#8b5cf6", border: "#7c3aed", label: "Tumoral" },
  autoimmun:    { color: "#ec4899", border: "#db2777", label: "Auto-immun" },
  fonctionnel:  { color: "#f59e0b", border: "#d97706", label: "Fonctionnel" },
  diagnostic:   { color: "#3b82f6", border: "#2563eb", label: "Diagnostic" },
  traitement:   { color: "#10b981", border: "#059669", label: "Traitement" },
  anatomie:     { color: "#14b8a6", border: "#0d9488", label: "Anatomie" },
};

const NODES = [
  // Core
  { id: "dermatologie", cat: "core", x: 600, y: 400 },

  // Inflammatoire
  { id: "eczéma", cat: "inflammatoire", x: 200, y: 150 },
  { id: "dermatite atopique", cat: "inflammatoire", x: 100, y: 90 },
  { id: "dermatite contact", cat: "inflammatoire", x: 80, y: 180 },
  { id: "psoriasis", cat: "inflammatoire", x: 300, y: 80 },
  { id: "psoriasis en plaques", cat: "inflammatoire", x: 400, y: 30 },
  { id: "psoriasis unguéal", cat: "inflammatoire", x: 240, y: 20 },
  { id: "rosacea", cat: "inflammatoire", x: 140, y: 260 },
  { id: "acné", cat: "inflammatoire", x: 320, y: 180 },
  { id: "acné rétentionnelle", cat: "inflammatoire", x: 420, y: 120 },
  { id: "acné inflammatoire", cat: "inflammatoire", x: 430, y: 200 },
  { id: "urticaire", cat: "inflammatoire", x: 60, y: 340 },
  { id: "dermatite séborrhéique", cat: "inflammatoire", x: 200, y: 330 },
  { id: "lichen plan", cat: "inflammatoire", x: 100, y: 430 },
  { id: "érythème", cat: "inflammatoire", x: 50, y: 260 },

  // Infectieux
  { id: "mycose", cat: "infectieux", x: 110, y: 530 },
  { id: "dermatophytose", cat: "infectieux", x: 50, y: 600 },
  { id: "candidose", cat: "infectieux", x: 160, y: 620 },
  { id: "onychomycose", cat: "infectieux", x: 80, y: 680 },
  { id: "verrue", cat: "infectieux", x: 240, y: 550 },
  { id: "herpès", cat: "infectieux", x: 300, y: 620 },
  { id: "zona", cat: "infectieux", x: 370, y: 570 },
  { id: "impétigo", cat: "infectieux", x: 200, y: 680 },
  { id: "cellulite", cat: "infectieux", x: 310, y: 700 },
  { id: "gale", cat: "infectieux", x: 420, y: 650 },
  { id: "molluscum", cat: "infectieux", x: 170, y: 470 },

  // Tumoral
  { id: "mélanome", cat: "tumoral", x: 900, y: 80 },
  { id: "carcinome basocellulaire", cat: "tumoral", x: 1020, y: 50 },
  { id: "carcinome épidermoïde", cat: "tumoral", x: 1080, y: 140 },
  { id: "nævus", cat: "tumoral", x: 800, y: 40 },
  { id: "kératose actinique", cat: "tumoral", x: 1000, y: 180 },
  { id: "kératose séborrhéique", cat: "tumoral", x: 830, y: 150 },
  { id: "lésion pigmentée", cat: "tumoral", x: 750, y: 100 },
  { id: "lymphome cutané", cat: "tumoral", x: 1100, y: 60 },

  // Auto-immun
  { id: "lupus cutané", cat: "autoimmun", x: 950, y: 280 },
  { id: "vitiligo", cat: "autoimmun", x: 1050, y: 340 },
  { id: "sclérodermie", cat: "autoimmun", x: 1100, y: 250 },
  { id: "pemphigus", cat: "autoimmun", x: 1030, y: 420 },
  { id: "pemphigoïde", cat: "autoimmun", x: 1120, y: 350 },
  { id: "dermatomyosite", cat: "autoimmun", x: 960, y: 380 },
  { id: "alopécie areata", cat: "autoimmun", x: 870, y: 310 },

  // Fonctionnel / Annexes
  { id: "alopécie", cat: "fonctionnel", x: 800, y: 260 },
  { id: "alopécie androgénique", cat: "fonctionnel", x: 730, y: 200 },
  { id: "hirsutisme", cat: "fonctionnel", x: 700, y: 280 },
  { id: "hyperhidrose", cat: "fonctionnel", x: 650, y: 210 },
  { id: "prurit", cat: "fonctionnel", x: 540, y: 180 },
  { id: "xérose", cat: "fonctionnel", x: 500, y: 250 },
  { id: "cicatrice", cat: "fonctionnel", x: 580, y: 280 },
  { id: "chéloïde", cat: "fonctionnel", x: 650, y: 340 },
  { id: "photosensibilité", cat: "fonctionnel", x: 550, y: 120 },

  // Diagnostic
  { id: "dermoscopie", cat: "diagnostic", x: 800, y: 500 },
  { id: "biopsie cutanée", cat: "diagnostic", x: 900, y: 550 },
  { id: "histopathologie", cat: "diagnostic", x: 1000, y: 520 },
  { id: "patch test", cat: "diagnostic", x: 680, y: 520 },
  { id: "lampe de Wood", cat: "diagnostic", x: 750, y: 580 },
  { id: "photographie clinique", cat: "diagnostic", x: 850, y: 620 },
  { id: "IA dermatoscopique", cat: "diagnostic", x: 950, y: 610 },
  { id: "culture mycologique", cat: "diagnostic", x: 680, y: 620 },

  // Traitement
  { id: "corticothérapie locale", cat: "traitement", x: 450, y: 380 },
  { id: "photothérapie", cat: "traitement", x: 500, y: 460 },
  { id: "rétinoïdes", cat: "traitement", x: 380, y: 440 },
  { id: "antifongiques", cat: "traitement", x: 350, y: 530 },
  { id: "antibiothérapie", cat: "traitement", x: 450, y: 560 },
  { id: "immunosuppresseurs", cat: "traitement", x: 560, y: 520 },
  { id: "biothérapie", cat: "traitement", x: 560, y: 440 },
  { id: "chirurgie dermatologique", cat: "traitement", x: 650, y: 450 },
  { id: "cryothérapie", cat: "traitement", x: 380, y: 350 },
  { id: "laser", cat: "traitement", x: 500, y: 370 },
  { id: "émollients", cat: "traitement", x: 320, y: 380 },

  // Anatomie
  { id: "épiderme", cat: "anatomie", x: 1050, y: 500 },
  { id: "derme", cat: "anatomie", x: 1100, y: 560 },
  { id: "hypoderme", cat: "anatomie", x: 1080, y: 630 },
  { id: "follicule pileux", cat: "anatomie", x: 1150, y: 470 },
  { id: "glande sébacée", cat: "anatomie", x: 1150, y: 540 },
  { id: "ongle", cat: "anatomie", x: 1130, y: 680 },
  { id: "mélanocyte", cat: "anatomie", x: 1000, y: 680 },
];

const EDGES = [
  // Core
  { s: "dermatologie", t: "eczéma", l: "traite" }, { s: "dermatologie", t: "psoriasis", l: "traite" },
  { s: "dermatologie", t: "acné", l: "traite" }, { s: "dermatologie", t: "mélanome", l: "dépiste" },
  { s: "dermatologie", t: "mycose", l: "traite" }, { s: "dermatologie", t: "dermoscopie", l: "utilise" },

  // Inflammatoire - hiérarchie
  { s: "eczéma", t: "dermatite atopique", l: "type" }, { s: "eczéma", t: "dermatite contact", l: "type" },
  { s: "psoriasis", t: "psoriasis en plaques", l: "type" }, { s: "psoriasis", t: "psoriasis unguéal", l: "type" },
  { s: "acné", t: "acné rétentionnelle", l: "type" }, { s: "acné", t: "acné inflammatoire", l: "type" },

  // Inflammatoire - relations
  { s: "dermatite atopique", t: "prurit", l: "symptôme" }, { s: "dermatite atopique", t: "xérose", l: "associée" },
  { s: "dermatite contact", t: "patch test", l: "diagnostiqué par" },
  { s: "psoriasis", t: "lichen plan", l: "diagnostic différentiel" },
  { s: "urticaire", t: "prurit", l: "symptôme" },
  { s: "acné", t: "glande sébacée", l: "siège" }, { s: "acné", t: "follicule pileux", l: "siège" },
  { s: "rosacea", t: "érythème", l: "symptôme" },

  // Infectieux - hiérarchie
  { s: "mycose", t: "dermatophytose", l: "type" }, { s: "mycose", t: "candidose", l: "type" },
  { s: "mycose", t: "onychomycose", l: "type" },
  { s: "herpès", t: "zona", l: "même famille" },

  // Infectieux - diagnostic
  { s: "mycose", t: "culture mycologique", l: "confirmée par" },
  { s: "mycose", t: "lampe de Wood", l: "dépistée par" },

  // Tumoral
  { s: "lésion pigmentée", t: "nævus", l: "inclut" }, { s: "lésion pigmentée", t: "mélanome", l: "peut être" },
  { s: "nævus", t: "mélanome", l: "risque de" },
  { s: "kératose actinique", t: "carcinome épidermoïde", l: "évolue vers" },
  { s: "mélanome", t: "mélanocyte", l: "origine" },
  { s: "carcinome basocellulaire", t: "épiderme", l: "origine" },
  { s: "carcinome épidermoïde", t: "épiderme", l: "origine" },

  // Tumoral - diagnostic
  { s: "lésion pigmentée", t: "dermoscopie", l: "évaluée par" },
  { s: "mélanome", t: "biopsie cutanée", l: "confirmé par" },
  { s: "dermoscopie", t: "IA dermatoscopique", l: "assistée par" },
  { s: "biopsie cutanée", t: "histopathologie", l: "analysée par" },

  // Auto-immun
  { s: "lupus cutané", t: "photosensibilité", l: "facteur" },
  { s: "vitiligo", t: "mélanocyte", l: "destruction" },
  { s: "pemphigus", t: "épiderme", l: "atteint" },
  { s: "pemphigoïde", t: "derme", l: "jonction" },
  { s: "alopécie areata", t: "alopécie", l: "type" },
  { s: "alopécie areata", t: "follicule pileux", l: "cible" },

  // Fonctionnel
  { s: "alopécie", t: "alopécie androgénique", l: "type" },
  { s: "cicatrice", t: "chéloïde", l: "complication" },
  { s: "photosensibilité", t: "mélanome", l: "facteur de risque" },

  // Traitements
  { s: "dermatite atopique", t: "corticothérapie locale", l: "traité par" },
  { s: "dermatite atopique", t: "émollients", l: "traité par" },
  { s: "psoriasis", t: "photothérapie", l: "traité par" },
  { s: "psoriasis", t: "biothérapie", l: "traité par" },
  { s: "psoriasis", t: "corticothérapie locale", l: "traité par" },
  { s: "acné", t: "rétinoïdes", l: "traité par" },
  { s: "acné inflammatoire", t: "antibiothérapie", l: "traité par" },
  { s: "mycose", t: "antifongiques", l: "traité par" },
  { s: "impétigo", t: "antibiothérapie", l: "traité par" },
  { s: "cellulite", t: "antibiothérapie", l: "traité par" },
  { s: "verrue", t: "cryothérapie", l: "traité par" },
  { s: "lupus cutané", t: "immunosuppresseurs", l: "traité par" },
  { s: "pemphigus", t: "immunosuppresseurs", l: "traité par" },
  { s: "mélanome", t: "chirurgie dermatologique", l: "traité par" },
  { s: "carcinome basocellulaire", t: "chirurgie dermatologique", l: "traité par" },
  { s: "chéloïde", t: "laser", l: "traité par" },
  { s: "chéloïde", t: "corticothérapie locale", l: "traité par" },

  // Anatomie couches
  { s: "épiderme", t: "derme", l: "repose sur" }, { s: "derme", t: "hypoderme", l: "repose sur" },
  { s: "follicule pileux", t: "derme", l: "logé dans" }, { s: "glande sébacée", t: "follicule pileux", l: "annexée à" },
  { s: "ongle", t: "épiderme", l: "dérivé de" }, { s: "mélanocyte", t: "épiderme", l: "situé dans" },
  { s: "psoriasis unguéal", t: "ongle", l: "atteint" }, { s: "onychomycose", t: "ongle", l: "atteint" },
];

export default function DermaKG() {
  const [hovered, setHovered] = useState(null);
  const [selected, setSelected] = useState(null);
  const [filterCat, setFilterCat] = useState(null);
  const svgRef = useRef(null);

  const nodeMap = useMemo(() => {
    const m = {};
    NODES.forEach(n => m[n.id] = n);
    return m;
  }, []);

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

  const activeEdges = useMemo(() =>
    activeId ? EDGES.filter(e => e.s === activeId || e.t === activeId) : [],
  [activeId]);

  const getOp = useCallback((n) => {
    if (n.id === "dermatologie") return 1;
    if (filterCat && n.cat !== filterCat) return 0.05;
    if (activeId && !connectedIds.has(n.id)) return 0.1;
    return 1;
  }, [filterCat, activeId, connectedIds]);

  const cats = ["inflammatoire", "infectieux", "tumoral", "autoimmun", "fonctionnel", "diagnostic", "traitement", "anatomie"];

  return (
    <div style={{ background: "#0a0a0f", minHeight: "100vh", fontFamily: "'Segoe UI',system-ui,sans-serif", color: "#e2e8f0", padding: 12 }}>
      <div style={{ textAlign: "center", marginBottom: 8 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 4px" }}>🩺 Knowledge Graph — Dermatologie</h1>
        <p style={{ fontSize: 12, color: "#94a3b8", margin: 0 }}>{NODES.length} nœuds · {EDGES.length} relations · Survolez ou cliquez pour explorer</p>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, justifyContent: "center", marginBottom: 8 }}>
        <button onClick={() => { setFilterCat(null); setSelected(null); }}
          style={{ padding: "3px 10px", borderRadius: 6, border: !filterCat ? "2px solid #c084fc" : "1px solid #475569", background: !filterCat ? "#1e1b4b" : "#1e293b", color: "#e2e8f0", fontSize: 11, cursor: "pointer" }}>Tout</button>
        {cats.map(c => (
          <button key={c} onClick={() => { setFilterCat(filterCat === c ? null : c); setSelected(null); }}
            style={{ padding: "3px 10px", borderRadius: 6, border: filterCat === c ? `2px solid ${CAT_META[c].color}` : "1px solid #475569",
              background: filterCat === c ? CAT_META[c].color + "22" : "#1e293b", color: CAT_META[c].color, fontSize: 11, cursor: "pointer" }}>
            {CAT_META[c].label}
          </button>
        ))}
      </div>

      <svg ref={svgRef} viewBox="0 0 1200 750" style={{ width: "100%", maxHeight: "70vh", borderRadius: 12, border: "1px solid #1e293b", background: "#0f172a" }}>
        <defs>
          <marker id="da" markerWidth="6" markerHeight="5" refX="6" refY="2.5" orient="auto"><polygon points="0 0,6 2.5,0 5" fill="#475569" /></marker>
          <marker id="daa" markerWidth="6" markerHeight="5" refX="6" refY="2.5" orient="auto"><polygon points="0 0,6 2.5,0 5" fill="#a78bfa" /></marker>
          <filter id="dgl"><feGaussianBlur stdDeviation="4" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        </defs>

        {EDGES.map((e, i) => {
          const sn = nodeMap[e.s], tn = nodeMap[e.t];
          if (!sn || !tn) return null;
          const isA = activeId && (e.s === activeId || e.t === activeId);
          return (
            <g key={`e${i}`}>
              <line x1={sn.x} y1={sn.y} x2={tn.x} y2={tn.y}
                stroke={isA ? "#a78bfa" : "#334155"} strokeWidth={isA ? 1.5 : 0.5}
                opacity={isA ? 1 : (activeId ? 0.05 : 0.18)} markerEnd={isA ? "url(#daa)" : "url(#da)"} />
              {isA && <text x={(sn.x+tn.x)/2} y={(sn.y+tn.y)/2-5} textAnchor="middle" fill="#c4b5fd" fontSize="7" fontStyle="italic">{e.l}</text>}
            </g>
          );
        })}

        {NODES.map(n => {
          const meta = CAT_META[n.cat] || CAT_META.core;
          const isCore = n.id === "dermatologie";
          const isA = activeId === n.id;
          const op = getOp(n);
          const r = isCore ? 32 : (n.id.length > 20 ? 24 : 19);
          const label = n.id.length > 24 ? n.id.slice(0, 22) + "…" : n.id;

          return (
            <g key={n.id} opacity={op} style={{ cursor: "pointer", transition: "opacity 0.2s" }}
              onMouseEnter={() => setHovered(n.id)} onMouseLeave={() => setHovered(null)}
              onClick={() => setSelected(s => s === n.id ? null : n.id)}>
              {isA && <circle cx={n.x} cy={n.y} r={r+5} fill="none" stroke="#a78bfa" strokeWidth={2} filter="url(#dgl)" />}
              <circle cx={n.x} cy={n.y} r={r} fill={meta.color} stroke={meta.border} strokeWidth={1.5} />
              <text x={n.x} y={n.y+0.5} textAnchor="middle" dominantBaseline="central"
                fill="#fff" fontSize={isCore ? 11 : 7.5} fontWeight={isCore ? 700 : 500}>{label}</text>
            </g>
          );
        })}
      </svg>

      {selected && nodeMap[selected] && (
        <div style={{ marginTop: 10, background: "#1e293b", border: "1px solid #334155", borderRadius: 10, padding: 14, maxWidth: 500, margin: "10px auto 0" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <div style={{ width: 12, height: 12, borderRadius: "50%", background: (CAT_META[nodeMap[selected].cat] || {}).color || "#6366f1" }} />
            <strong style={{ fontSize: 15 }}>{nodeMap[selected].id}</strong>
            <span style={{ fontSize: 11, color: "#94a3b8", marginLeft: "auto" }}>{nodeMap[selected].cat}</span>
          </div>
          <div style={{ fontSize: 13 }}>
            {activeEdges.length === 0 && <span style={{ color: "#64748b" }}>Aucune relation</span>}
            {activeEdges.map((e, i) => {
              const isS = e.s === selected;
              const other = nodeMap[isS ? e.t : e.s];
              return other ? (
                <div key={i} style={{ padding: "2px 0", display: "flex", gap: 6, alignItems: "center" }}>
                  <span style={{ color: "#64748b" }}>{isS ? "→" : "←"}</span>
                  <span style={{ color: "#c4b5fd", fontStyle: "italic", fontSize: 11 }}>{e.l}</span>
                  <span>{other.id}</span>
                </div>
              ) : null;
            })}
          </div>
        </div>
      )}
    </div>
  );
}
