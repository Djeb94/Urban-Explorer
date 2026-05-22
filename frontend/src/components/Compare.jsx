import { useEffect, useState } from "react"
import axios from "axios"
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts"

const API = "http://localhost:8000"

const INDICATEURS = [
  { key: "accessibilite_achat", label: "Accessibilité", route: "ind1", max: 25 },
  { key: "score_vivabilite",    label: "Vivabilité",    route: "ind2", max: 1 },
  { key: "score_attractivite",  label: "Attractivité",  route: "ind3", max: 1 },
  { key: "mixite_sociale",      label: "Mixité",        route: "ind4", max: 10 }
]

export default function Compare({ selected, compared }) {
  const [dataA, setDataA] = useState({})
  const [dataB, setDataB] = useState({})

  useEffect(() => {
    if (!selected) return
    Promise.all(INDICATEURS.map(i => axios.get(`${API}/${i.route}/${selected}`))).then(results => {
      const merged = {}
      results.forEach((r, i) => { merged[INDICATEURS[i].key] = r.data[INDICATEURS[i].key] })
      setDataA(merged)
    })
  }, [selected])

  useEffect(() => {
    if (!compared) return
    Promise.all(INDICATEURS.map(i => axios.get(`${API}/${i.route}/${compared}`))).then(results => {
      const merged = {}
      results.forEach((r, i) => { merged[INDICATEURS[i].key] = r.data[INDICATEURS[i].key] })
      setDataB(merged)
    })
  }, [compared])

  const normalize = (key, val) => {
    const ind = INDICATEURS.find(i => i.key === key)
    return Math.min(Math.round((val || 0) / ind.max * 100) / 100, 1)
  }

  const radarData = INDICATEURS.map(ind => ({
    indicateur: ind.label,
    [selected + "ème"]: normalize(ind.key, dataA[ind.key]),
    [compared + "ème"]: normalize(ind.key, dataB[ind.key]),
  }))

  return (
    <div style={{
      background: "#161b27", borderTop: "1px solid #2a2f3e",
      padding: "16px 32px", display: "flex", gap: 40, alignItems: "center",
      height: 280
    }}>
      <div style={{ width: 420, height: 260, display: "flex", flexDirection: "column" }}>
        <p style={{ fontSize: 11, color: "#8892a4", textTransform: "uppercase", marginBottom: 4 }}>
          Comparaison — {selected}ème vs {compared}ème
        </p>
        <div style={{ display: "flex", gap: 16, marginBottom: 6 }}>
          <span style={{ fontSize: 12, color: "#3b82f6" }}>— {selected}ème</span>
          <span style={{ fontSize: 12, color: "#f44336" }}>— {compared}ème</span>
        </div>
        <ResponsiveContainer width="100%" height={210}>
          <RadarChart data={radarData} outerRadius={75} margin={{ top: 10, right: 70, bottom: 10, left: 70 }}>
          <PolarGrid gridType="polygon" stroke="#ffffff40" strokeWidth={1} />
            <PolarAngleAxis dataKey="indicateur" tick={{ fill: "#8892a4", fontSize: 11 }} />
            <PolarRadiusAxis domain={[0, 1]} tick={false} axisLine={false} />
            <Radar dataKey={selected + "ème"} stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.5} />
            <Radar dataKey={compared + "ème"} stroke="#f44336" fill="#f44336" fillOpacity={0.5} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      <div style={{ flex: 1 }}>
        {INDICATEURS.map(ind => (
          <div key={ind.key} style={{
            display: "flex", alignItems: "center", gap: 10,
            marginBottom: 16, fontSize: 13
          }}>
            <span style={{ color: "#8892a4", width: 90 }}>{ind.label}</span>
            <div style={{ flex: 1, background: "#1e2433", borderRadius: 4, height: 10, position: "relative" }}>
              <div style={{
                position: "absolute", left: 0, top: 0, height: "100%",
                width: `${normalize(ind.key, dataA[ind.key]) * 100}%`,
                background: "#3b82f6", borderRadius: 4
              }} />
            </div>
            <span style={{ color: "#3b82f6", width: 40, textAlign: "right" }}>
              {(dataA[ind.key] || 0).toFixed(2)}
            </span>
            <div style={{ flex: 1, background: "#1e2433", borderRadius: 4, height: 10, position: "relative" }}>
              <div style={{
                position: "absolute", left: 0, top: 0, height: "100%",
                width: `${normalize(ind.key, dataB[ind.key]) * 100}%`,
                background: "#f44336", borderRadius: 4
              }} />
            </div>
            <span style={{ color: "#f44336", width: 40, textAlign: "right" }}>
              {(dataB[ind.key] || 0).toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}