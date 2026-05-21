import { useState, useEffect } from "react"
import axios from "axios"

const API = "http://localhost:8000"

const INDICATEURS = [
  { value: "accessibilite_achat", label: "Accessibilité à l'achat", route: "ind1" },
  { value: "pression_immo",       label: "Pression immobilière",    route: "ind2" },
  { value: "score_attractivite",  label: "Score attractivité",      route: "ind3" },
  { value: "mixite_sociale",      label: "Mixité sociale",          route: "ind4" }
]

export default function Sidebar({ data, selected, indicateur, setIndicateur, ind1, ind2, ind3, ind4 }) {
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

      {/* Titre */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 18, fontWeight: 700, color: "#fff" }}>
          🏙️ Urban Data Explorer
        </h1>
        <p style={{ fontSize: 12, color: "#8892a4", marginTop: 4 }}>
          Paris — Données immobilières
        </p>
      </div>

      {/* Sélecteur indicateur */}
      <div style={{ marginBottom: 20 }}>
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

      {/* Détail arrondissement sélectionné */}
      {selected && detail && (
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

      {/* Classement */}
      <div>
        <p style={{ fontSize: 11, color: "#8892a4", marginBottom: 8, textTransform: "uppercase" }}>
          Classement
        </p>
        {sorted.map((row, i) => (
          <div key={row.arrondissement} style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "6px 10px", marginBottom: 3, borderRadius: 6, cursor: "pointer",
            background: selected === row.arrondissement ? "#3b82f6" : "#1e2433",
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