import { useState, useEffect, useRef, useCallback } from "react";

const NODES = [
  // Central
  { id: "orthodontie", label: "Orthodontie", category: "core", x: 400, y: 300 },

  // Pathologies
  { id: "malocclusion", label: "Malocclusion", category: "pathology", x: 180, y: 120 },
  { id: "classe1", label: "Classe I", category: "pathology", x: 60, y: 40 },
  { id: "classe2", label: "Classe II", category: "pathology", x: 180, y: 20 },
  { id: "classe3", label: "Classe III", category: "pathology", x: 300, y: 40 },
  { id: "encombrement", label: "Encombrement\ndentaire", category: "pathology", x: 80, y: 200 },
  { id: "beance", label: "Béance", category: "pathology", x: 60, y: 300 },
  { id: "supraclusion", label: "Supraclusion", category: "pathology", x: 60, y: 380 },

  // Traitements
  { id: "traitements", label: "Traitements", category: "treatment", x: 620, y: 120 },
  { id: "bagues", label: "Bagues\nmétalliques", category: "treatment", x: 700, y: 30 },
  { id: "aligneurs", label: "Aligneurs\ntransparents", category: "treatment", x: 760, y: 120 },
  { id: "appareils_fn", label: "Appareils\nfonctionnels", category: "treatment", x: 750, y: 210 },
  { id: "contention", label: "Contention", category: "treatment", x: 650, y: 270 },
  { id: "chirurgie", label: "Chirurgie\northognathique", category: "treatment", x: 520, y: 50 },

  // Anatomie
  { id: "anatomie", label: "Anatomie", category: "anatomy", x: 250, y: 450 },
  { id: "maxillaire", label: "Maxillaire", category: "anatomy", x: 120, y: 500 },
  { id: "mandibule", label: "Mandibule", category: "anatomy", x: 250, y: 540 },
  { id: "atm", label: "ATM", category: "anatomy", x: 380, y: 520 },
  { id: "dents", label: "Dents", category: "anatomy", x: 160, y: 440 },

  // Diagnostic
  { id: "diagnostic", label: "Diagnostic", category: "diagnostic", x: 550, y: 450 },
  { id: "cephalo", label: "Céphalométrie", category: "diagnostic", x: 650, y: 520 },
  { id: "panoramique", label: "Radio\npanoramique", category: "diagnostic", x: 500, y: 550 },
  { id: "empreintes", label: "Empreintes\nnumériques", category: "diagnostic", x: 720, y: 430 },
  { id: "photo", label: "Photos\ncliniques", category: "diagnostic", x: 700, y: 350 },

  // Biomécanique
  { id: "biomecanique", label: "Biomécanique", category: "bio", x: 400, y: 160 },
  { id: "forces", label: "Forces\northodontiques", category: "bio", x: 350, y: 80 },
  { id: "ancrage", label: "Ancrage", category: "bio", x: 480, y: 80 },
  { id: "resorption", label: "Résorption\nradiculaire", category: "bio", x: 480, y: 180 },
];

const EDGES = [
  // Core connections
  { source: "orthodontie", target: "malocclusion", label: "traite" },
  { source: "orthodontie", target: "traitements", label: "utilise" },
  { source: "orthodontie", target: "anatomie", label: "étudie" },
  { source: "orthodontie", target: "diagnostic", label: "requiert" },
  { source: "orthodontie", target: "biomecanique", label: "applique" },

  // Malocclusion subtypes
  { source: "malocclusion", target: "classe1", label: "type" },
  { source: "malocclusion", target: "classe2", label: "type" },
  { source: "malocclusion", target: "classe3", label: "type" },
  { source: "malocclusion", target: "encombrement", label: "inclut" },
  { source: "malocclusion", target: "beance", label: "inclut" },
  { source: "malocclusion", target: "supraclusion", label: "inclut" },

  // Traitements
  { source: "traitements", target: "bagues", label: "type" },
  { source: "traitements", target: "aligneurs", label: "type" },
  { source: "traitements", target: "appareils_fn", label: "type" },
  { source: "traitements", target: "contention", label: "suivi par" },
  { source: "traitements", target: "chirurgie", label: "combiné à" },
  { source: "classe2", target: "appareils_fn", label: "traité par" },
  { source: "classe3", target: "chirurgie", label: "peut nécessiter" },
  { source: "encombrement", target: "bagues", label: "traité par" },
  { source: "encombrement", target: "aligneurs", label: "traité par" },

  // Anatomie
  { source: "anatomie", target: "maxillaire", label: "comprend" },
  { source: "anatomie", target: "mandibule", label: "comprend" },
  { source: "anatomie", target: "atm", label: "comprend" },
  { source: "anatomie", target: "dents", label: "comprend" },
  { source: "atm", target: "malocclusion", label: "affectée par" },

  // Diagnostic
  { source: "diagnostic", target: "cephalo", label: "utilise" },
  { source: "diagnostic", target: "panoramique", label: "utilise" },
  { source: "diagnostic", target: "empreintes", label: "utilise" },
  { source: "diagnostic", target: "photo", label: "utilise" },
  { source: "cephalo", target: "biomecanique", label: "guide" },

  // Biomécanique
  { source: "biomecanique", target: "forces", label: "applique" },
  { source: "biomecanique", target: "ancrage", label: "nécessite" },
  { source: "biomecanique", target: "resorption", label: "risque" },
  { source: "forces", target: "dents", label: "agissent sur" },
  { source: "ancrage", target: "bagues", label: "fourni par" },
];

const CATEGORY_COLORS = {
  core: { bg: "#6366f1", border: "#4f46e5", text: "#ffffff" },
  pathology: { bg: "#ef4444", border: "#dc2626", text: "#ffffff" },
  treatment: { bg: "#10b981", border: "#059669", text: "#ffffff" },
  anatomy: { bg: "#f59e0b", border: "#d97706", text: "#ffffff" },
  diagnostic: { bg: "#3b82f6", border: "#2563eb", text: "#ffffff" },
  bio: { bg: "#8b5cf6", border: "#7c3aed", text: "#ffffff" },
};

const CATEGORY_LABELS = {
  core: "Orthodontie",
  pathology: "Pathologies",
  treatment: "Traitements",
  anatomy: "Anatomie",
  diagnostic: "Diagnostic",
  bio: "Biomécanique",
};

export default function OrthodontieKG() {
  const svgRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [dragNode, setDragNode] = useState(null);
  const [nodes, setNodes] = useState(NODES);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  const getConnectedEdges = useCallback(
    (nodeId) => {
      if (!nodeId) return [];
      return EDGES.filter((e) => e.source === nodeId || e.target === nodeId);
    },
    []
  );

  const getConnectedNodes = useCallback(
    (nodeId) => {
      if (!nodeId) return new Set();
      const connected = new Set([nodeId]);
      EDGES.forEach((e) => {
        if (e.source === nodeId) connected.add(e.target);
        if (e.target === nodeId) connected.add(e.source);
      });
      return connected;
    },
    []
  );

  const activeNodeId = selectedNode || hoveredNode;
  const connectedNodes = getConnectedNodes(activeNodeId);
  const isFiltering = !!activeNodeId;

  const handleMouseDown = (e, nodeId) => {
    e.preventDefault();
    const svg = svgRef.current;
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());
    const node = nodes.find((n) => n.id === nodeId);
    setOffset({ x: svgP.x - node.x, y: svgP.y - node.y });
    setDragNode(nodeId);
  };

  const handleMouseMove = useCallback(
    (e) => {
      if (!dragNode) return;
      const svg = svgRef.current;
      const pt = svg.createSVGPoint();
      pt.x = e.clientX;
      pt.y = e.clientY;
      const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());
      setNodes((prev) =>
        prev.map((n) =>
          n.id === dragNode ? { ...n, x: svgP.x - offset.x, y: svgP.y - offset.y } : n
        )
      );
    },
    [dragNode, offset]
  );

  const handleMouseUp = useCallback(() => {
    setDragNode(null);
  }, []);

  useEffect(() => {
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

  const nodeMap = {};
  nodes.forEach((n) => (nodeMap[n.id] = n));

  return (
    <div className="w-full min-h-screen bg-gray-950 flex flex-col items-center p-4">
      <h1 className="text-2xl font-bold text-white mb-1">
        🦷 Knowledge Graph — Orthodontie
      </h1>
      <p className="text-gray-400 text-sm mb-3">
        Survolez ou cliquez un nœud pour explorer ses connexions • Glissez pour réorganiser
      </p>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mb-4 justify-center">
        {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
          <div key={key} className="flex items-center gap-1.5">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: CATEGORY_COLORS[key].bg }}
            />
            <span className="text-gray-300 text-xs">{label}</span>
          </div>
        ))}
      </div>

      <svg
        ref={svgRef}
        viewBox="0 0 800 600"
        className="w-full max-w-4xl rounded-xl border border-gray-800 bg-gray-900"
        style={{ cursor: dragNode ? "grabbing" : "default" }}
      >
        <defs>
          <marker
            id="arrowhead"
            markerWidth="8"
            markerHeight="6"
            refX="8"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 8 3, 0 6" fill="#64748b" />
          </marker>
          <marker
            id="arrowhead-active"
            markerWidth="8"
            markerHeight="6"
            refX="8"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 8 3, 0 6" fill="#c084fc" />
          </marker>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Edges */}
        {EDGES.map((edge, i) => {
          const s = nodeMap[edge.source];
          const t = nodeMap[edge.target];
          if (!s || !t) return null;

          const isActive =
            isFiltering &&
            (edge.source === activeNodeId || edge.target === activeNodeId);
          const isDimmed = isFiltering && !isActive;

          const mx = (s.x + t.x) / 2;
          const my = (s.y + t.y) / 2;

          return (
            <g key={i} opacity={isDimmed ? 0.08 : 1}>
              <line
                x1={s.x}
                y1={s.y}
                x2={t.x}
                y2={t.y}
                stroke={isActive ? "#c084fc" : "#475569"}
                strokeWidth={isActive ? 2 : 1}
                markerEnd={
                  isActive ? "url(#arrowhead-active)" : "url(#arrowhead)"
                }
              />
              {(isActive || !isFiltering) && (
                <text
                  x={mx}
                  y={my - 6}
                  textAnchor="middle"
                  fill={isActive ? "#e9d5ff" : "#94a3b8"}
                  fontSize="8"
                  fontStyle="italic"
                >
                  {edge.label}
                </text>
              )}
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map((node) => {
          const color = CATEGORY_COLORS[node.category];
          const isActive = activeNodeId === node.id;
          const isConnected = connectedNodes.has(node.id);
          const isDimmed = isFiltering && !isConnected;
          const isCore = node.category === "core";
          const r = isCore ? 36 : 26;
          const lines = node.label.split("\n");

          return (
            <g
              key={node.id}
              transform={`translate(${node.x}, ${node.y})`}
              opacity={isDimmed ? 0.12 : 1}
              style={{ cursor: dragNode === node.id ? "grabbing" : "pointer" }}
              onMouseEnter={() => !dragNode && setHoveredNode(node.id)}
              onMouseLeave={() => setHoveredNode(null)}
              onClick={() =>
                setSelectedNode((prev) =>
                  prev === node.id ? null : node.id
                )
              }
              onMouseDown={(e) => handleMouseDown(e, node.id)}
            >
              <circle
                r={r + 4}
                fill="transparent"
                stroke={isActive ? "#c084fc" : "transparent"}
                strokeWidth="2"
                filter={isActive ? "url(#glow)" : undefined}
              />
              <circle
                r={r}
                fill={color.bg}
                stroke={color.border}
                strokeWidth="2"
              />
              {lines.map((line, li) => (
                <text
                  key={li}
                  textAnchor="middle"
                  dy={
                    lines.length === 1
                      ? "0.35em"
                      : `${(li - (lines.length - 1) / 2) * 1.1 + 0.35}em`
                  }
                  fill={color.text}
                  fontSize={isCore ? "11" : "9"}
                  fontWeight={isCore ? "bold" : "600"}
                >
                  {line}
                </text>
              ))}
            </g>
          );
        })}
      </svg>

      {/* Info panel */}
      {selectedNode && (
        <div className="mt-4 bg-gray-800 border border-gray-700 rounded-lg p-4 max-w-md w-full">
          <div className="flex items-center gap-2 mb-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{
                backgroundColor:
                  CATEGORY_COLORS[nodeMap[selectedNode]?.category]?.bg,
              }}
            />
            <span className="text-white font-semibold">
              {nodeMap[selectedNode]?.label.replace("\n", " ")}
            </span>
            <span className="text-gray-500 text-xs ml-auto">
              {CATEGORY_LABELS[nodeMap[selectedNode]?.category]}
            </span>
          </div>
          <div className="text-gray-300 text-sm space-y-1">
            {getConnectedEdges(selectedNode).map((e, i) => {
              const isSource = e.source === selectedNode;
              const otherId = isSource ? e.target : e.source;
              const other = nodeMap[otherId];
              return (
                <div key={i} className="flex items-center gap-1.5">
                  <span className="text-gray-500">{isSource ? "→" : "←"}</span>
                  <span className="text-purple-300 italic text-xs">
                    {e.label}
                  </span>
                  <span>{other?.label.replace("\n", " ")}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <p className="text-gray-600 text-xs mt-4">
        {nodes.length} nœuds • {EDGES.length} relations • Classification d'Angle
      </p>
    </div>
  );
}
