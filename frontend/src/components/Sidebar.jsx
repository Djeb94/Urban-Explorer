import { useState, useEffect } from "react"
import axios from "axios"
import Charts from "./Charts"

const API = "http://localhost:8000"

const INDICATEURS = [
  { value: "accessibilite_achat", label: "Accessibilité à l'achat", route: "ind1" },
  { value: "score_vivabilite",    label: "Vivabilité urbaine",       route: "ind2" },
  { value: "score_attractivite",  label: "Score attractivité",       route: "ind3" },
  { value: "mixite_sociale",      label: "Mixité sociale",           route: "ind4" }
]

const COUCHES = [
  { value: "criminalite",        label: "Criminalité",        color: "#ef4444" },
  { value: "logements_sociaux",  label: "Logements sociaux",  color: "#22c55e" },
  { value: "espaces_verts",      label: "Espaces verts",      color: "#84cc16" },
  { value: "stations",           label: "Transports RATP",    color: "#f59e0b" },
]

export default function Sidebar({ data, selected, compared, indicateur, setIndicateur, compareMode, setCompareMode, setSelected, setCompared, activeCouche, setActiveCouche }) {
  const [detail, setDetail] = useState(null)

  useEffect(() => {
    if (!selected) return
    const route = INDICATEURS.find(i => i.value === indicateur)?.route
    axios.get(`${API}/${route}/${selected}`).then(res => setDetail(res.data))
  }, [selected, indicateur])

  const sorted = [...data].sort((a, b) => b[indicateur] - a[indicateur])

  return (
    <div style={{
      width: 320, background: "#161b27", display: "flex",
      flexDirection: "column", padding: 20, overflowY: "auto",
      borderRight: "1px solid #2a2f3e"
    }}>

      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 18, fontWeight: 700, color: "#fff" }}>
          Urban Data Explorer
        </h1>
        <p style={{ fontSize: 12, color: "#8892a4", marginTop: 4 }}>
          Paris — Données immobilières
        </p>
      </div>

      {/* Indicateurs */}
      <div style={{ marginBottom: 12 }}>
        <p style={{ fontSize: 11, color: "#8892a4", marginBottom: 8, textTransform: "uppercase" }}>
          Indicateur
        </p>
        {INDICATEURS.map(ind => (
          <button key={ind.value} onClick={() => setIndicateur(ind.value)} style={{
            display: "block", width: "100%", textAlign: "left",
            padding: "8px 12px", marginBottom: 4, borderRadius: 6,
            border: "none", cursor: "pointer", fontSize: 13,
            background: indicateur === ind.value ? "#3b82f6" : "#1e2433",
            color: indicateur === ind.value ? "#fff" : "#8892a4"
          }}>
            {ind.label}
          </button>
        ))}
      </div>

      {/* Couches superposées */}
      <div style={{ marginBottom: 16 }}>
        <p style={{ fontSize: 11, color: "#8892a4", marginBottom: 8, textTransform: "uppercase" }}>
          Couches
        </p>
        {COUCHES.map(c => (
          <button key={c.value} onClick={() => setActiveCouche(activeCouche === c.value ? null : c.value)} style={{
            display: "block", width: "100%", textAlign: "left",
            padding: "8px 12px", marginBottom: 4, borderRadius: 6,
            border: `1px solid ${activeCouche === c.value ? c.color : "transparent"}`,
            cursor: "pointer", fontSize: 13,
            background: activeCouche === c.value ? `${c.color}20` : "#1e2433",
            color: activeCouche === c.value ? c.color : "#8892a4"
          }}>
            {c.label}
          </button>
        ))}
      </div>

      {/* Mode comparaison */}
      <button onClick={() => { setCompareMode(!compareMode); setCompared(null); setSelected(null) }} style={{
        display: "block", width: "100%", textAlign: "center",
        padding: "8px 12px", marginBottom: 16, borderRadius: 6,
        border: `1px solid ${compareMode ? "#f44336" : "#3b82f6"}`,
        cursor: "pointer", fontSize: 13,
        background: compareMode ? "#f4433620" : "#3b82f620",
        color: compareMode ? "#f44336" : "#3b82f6"
      }}>
        {compareMode ? "Quitter comparaison" : "Mode comparaison"}
      </button>

      {compareMode && (
        <div style={{
          background: "#1e2433", borderRadius: 8, padding: 12,
          marginBottom: 16, fontSize: 12, color: "#8892a4",
          border: "1px solid #3b82f6"
        }}>
          {!selected && <p>Cliquez sur un 1er arrondissement</p>}
          {selected && !compared && <p>Cliquez sur un 2ème arrondissement<br/><b style={{color:"#3b82f6"}}>{selected}ème sélectionné</b></p>}
          {selected && compared && <p><b style={{color:"#3b82f6"}}>{selected}ème</b> vs <b style={{color:"#f44336"}}>{compared}ème</b></p>}
        </div>
      )}

      {selected && detail && !compareMode && (
        <div style={{
          background: "#1e2433", borderRadius: 8, padding: 16, marginBottom: 20,
          border: "1px solid #3b82f6"
        }}>
          <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>
            {selected}ème arrondissement
          </h2>
          {Object.entries(detail).map(([k, v]) => (
            k !== "arrondissement" && (
              <div key={k} style={{
                display: "flex", justifyContent: "space-between",
                marginBottom: 6, fontSize: 12
              }}>
                <span style={{ color: "#8892a4" }}>{k.replace(/_/g, " ")}</span>
                <span style={{ color: "#fff", fontWeight: 600 }}>
                  {typeof v === "number" ? v.toFixed(2) : v}
                </span>
              </div>
            )
          ))}
        </div>
      )}

      {!compareMode && <Charts selected={selected} />}

      <div>
        <p style={{ fontSize: 11, color: "#8892a4", marginBottom: 8, textTransform: "uppercase" }}>
          Classement
        </p>
        {sorted.map((row, i) => (
          <div key={row.arrondissement} style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "6px 10px", marginBottom: 3, borderRadius: 6, cursor: "pointer",
            background: selected === row.arrondissement ? "#3b82f6" :
                        compared === row.arrondissement ? "#f44336" : "#1e2433",
            fontSize: 12
          }}>
            <span style={{ color: "#8892a4", width: 20 }}>{i + 1}</span>
            <span style={{ flex: 1 }}>{Math.round(row.arrondissement)}ème</span>
            <span style={{ color: "#60a5fa", fontWeight: 600 }}>
              {row[indicateur]?.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}