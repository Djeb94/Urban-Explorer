import { useState, useEffect } from "react"
import axios from "axios"
import Map from "./components/Map"
import Sidebar from "./components/Sidebar"
import Compare from "./components/Compare"
import "./App.css"

const API = "http://localhost:8000"

export default function App() {
  const [ind1, setInd1] = useState([])
  const [ind2, setInd2] = useState([])
  const [ind3, setInd3] = useState([])
  const [ind4, setInd4] = useState([])
  const [selected, setSelected] = useState(null)
  const [compared, setCompared] = useState(null)
  const [indicateur, setIndicateur] = useState("accessibilite_achat")
  const [compareMode, setCompareMode] = useState(false)
  const [activeCouche, setActiveCouche] = useState(null)
  const [coucheData, setCoucheData] = useState([])

  useEffect(() => {
    axios.get(`${API}/ind1`).then(res => setInd1(res.data))
    axios.get(`${API}/ind2`).then(res => setInd2(res.data))
    axios.get(`${API}/ind3`).then(res => setInd3(res.data))
    axios.get(`${API}/ind4`).then(res => setInd4(res.data))
  }, [])

  useEffect(() => {
    if (!activeCouche) { setCoucheData([]); return }
    const routes = {
      criminalite: "/criminalite",
      logements_sociaux: "/logements-sociaux",
      espaces_verts: "/espaces-verts",
      stations: "/stations"
    }
    axios.get(`${API}${routes[activeCouche]}`).then(res => setCoucheData(res.data))
  }, [activeCouche])

  const getData = () => {
    if (indicateur === "accessibilite_achat") return ind1
    if (indicateur === "score_vivabilite")    return ind2
    if (indicateur === "score_attractivite")  return ind3
    if (indicateur === "mixite_sociale")      return ind4
    return ind1
  }

  const handleSelect = (arr) => {
    if (compareMode) {
      if (!selected) setSelected(arr)
      else if (arr !== selected) setCompared(arr)
    } else {
      setSelected(arr)
      setCompared(null)
    }
  }

  return (
    <div className="app">
      <Sidebar
        data={getData()}
        selected={selected}
        compared={compared}
        indicateur={indicateur}
        setIndicateur={setIndicateur}
        compareMode={compareMode}
        setCompareMode={setCompareMode}
        setSelected={setSelected}
        setCompared={setCompared}
        activeCouche={activeCouche}
        setActiveCouche={setActiveCouche}
      />
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ flex: 1, position: "relative", minHeight: 0 }}>
          <Map
            data={getData()}
            selected={selected}
            compared={compared}
            setSelected={handleSelect}
            indicateur={indicateur}
            activeCouche={activeCouche}
            coucheData={coucheData}
          />
        </div>
        {compareMode && selected && compared && (
          <div style={{ height: 280, flexShrink: 0 }}>
            <Compare selected={selected} compared={compared} indicateur={indicateur} />
          </div>
        )}
      </div>
    </div>
  )
}