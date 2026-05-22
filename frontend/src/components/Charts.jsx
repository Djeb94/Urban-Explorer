import { useEffect, useState } from "react"
import axios from "axios"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const API = "http://localhost:8000"

export default function Charts({ selected }) {
  const [timeline, setTimeline] = useState([])

  useEffect(() => {
    if (!selected) return
    axios.get(`${API}/timeline/${selected}`).then(res => setTimeline(res.data))
  }, [selected])

  if (!selected) return (
    <div style={{
      padding: 20, color: "#8892a4", fontSize: 13, textAlign: "center", marginTop: 20
    }}>
      Cliquez sur un arrondissement pour voir l'évolution des prix
    </div>
  )

  return (
    <div style={{ padding: "0 0 20px 0" }}>
      <p style={{
        fontSize: 11, color: "#8892a4", marginBottom: 12,
        textTransform: "uppercase", letterSpacing: 1
      }}>
        Évolution prix m² — {selected}ème arr.
      </p>

      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={timeline} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2f3e" />
          <XAxis dataKey="annee" stroke="#8892a4" fontSize={11} />
          <YAxis stroke="#8892a4" fontSize={11} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
          <Tooltip
            contentStyle={{ background: "#161b27", border: "1px solid #3b82f6", borderRadius: 6 }}
            labelStyle={{ color: "#fff" }}
            formatter={v => [`${v.toFixed(0)} €/m²`, "Prix médian"]}
          />
          <Line
            type="monotone"
            dataKey="prix_m2_median"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: "#3b82f6", r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>

      <div style={{
        display: "flex", justifyContent: "space-between",
        marginTop: 8, fontSize: 11, color: "#8892a4"
      }}>
        <span>Transactions : {timeline.reduce((a, b) => a + b.nb_transactions, 0).toLocaleString()}</span>
        {timeline.length > 1 && (
          <span style={{ color: timeline[timeline.length-1].prix_m2_median > timeline[0].prix_m2_median ? "#f44336" : "#22c55e" }}>
            {((timeline[timeline.length-1].prix_m2_median - timeline[0].prix_m2_median) / timeline[0].prix_m2_median * 100).toFixed(1)}% depuis 2021
          </span>
        )}
      </div>
    </div>
  )
}