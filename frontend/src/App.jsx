import { useState, useEffect } from "react"
import axios from "axios"
import Map from "./components/Map"
import Sidebar from "./components/Sidebar"
import "./App.css"

const API = "http://localhost:8000"

export default function App() {
  const [ind1, setInd1] = useState([])
  const [ind2, setInd2] = useState([])
  const [ind3, setInd3] = useState([])
  const [ind4, setInd4] = useState([])
  const [selected, setSelected] = useState(null)
  const [indicateur, setIndicateur] = useState("accessibilite_achat")

  useEffect(() => {
    axios.get(`${API}/ind1`).then(res => setInd1(res.data))
    axios.get(`${API}/ind2`).then(res => setInd2(res.data))
    axios.get(`${API}/ind3`).then(res => setInd3(res.data))
    axios.get(`${API}/ind4`).then(res => setInd4(res.data))
  }, [])

  const getData = () => {
    if (indicateur === "accessibilite_achat") return ind1
    if (indicateur === "pression_immo")       return ind2
    if (indicateur === "score_attractivite")  return ind3
    if (indicateur === "mixite_sociale")      return ind4
    return ind1
  }

  return (
    <div className="app">
      <Sidebar
        data={getData()}
        selected={selected}
        indicateur={indicateur}
        setIndicateur={setIndicateur}
        ind1={ind1} ind2={ind2} ind3={ind3} ind4={ind4}
      />
      <Map
        data={getData()}
        selected={selected}
        setSelected={setSelected}
        indicateur={indicateur}
      />
    </div>
  )
}