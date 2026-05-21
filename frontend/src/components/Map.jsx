import { useEffect, useRef, useState } from "react"
import maplibregl from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import axios from "axios"

const API = "http://localhost:8000"

const LABELS = {
  accessibilite_achat: "Accessibilité à l'achat",
  pression_immo: "Pression immobilière",
  score_attractivite: "Score attractivité",
  mixite_sociale: "Mixité sociale"
}

function getColor(value, min, max) {
  const t = (value - min) / (max - min)
  const r = Math.round(255 * t)
  const b = Math.round(255 * (1 - t))
  return `rgb(${r}, 50, ${b})`
}

export default function Map({ data, selected, setSelected, indicateur }) {
  const mapRef = useRef(null)
  const mapInstance = useRef(null)
  const [contours, setContours] = useState(null)

  useEffect(() => {
    axios.get(`${API}/contours`).then(res => setContours(res.data))
  }, [])

  useEffect(() => {
    if (!mapRef.current) return
    mapInstance.current = new maplibregl.Map({
      container: mapRef.current,
      style: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
      center: [2.3488, 48.8534],
      zoom: 11.5
    })
    mapInstance.current.addControl(new maplibregl.NavigationControl(), "top-right")
    return () => mapInstance.current.remove()
  }, [])

  useEffect(() => {
    if (!mapInstance.current || !contours || data.length === 0) return
    const map = mapInstance.current

    const addLayers = () => {
      const values = data.map(d => d[indicateur]).filter(Boolean)
      const min = Math.min(...values)
      const max = Math.max(...values)

      const geojson = {
        type: "FeatureCollection",
        features: contours.features.map(f => {
          const arr = f.properties.c_ar
          const row = data.find(d => Math.round(d.arrondissement) === arr)
          return {
            ...f,
            properties: {
              ...f.properties,
              value: row ? row[indicateur] : 0,
              arrondissement: arr
            }
          }
        })
      }

      if (map.getSource("arrondissements")) {
        map.getSource("arrondissements").setData(geojson)
      } else {
        map.addSource("arrondissements", { type: "geojson", data: geojson })

        map.addLayer({
          id: "fill-arr",
          type: "fill",
          source: "arrondissements",
          paint: {
            "fill-color": [
              "interpolate", ["linear"],
              ["get", "value"],
              min, "#1a237e",
              max, "#f44336"
            ],
            "fill-opacity": 0.7
          }
        })

        map.addLayer({
          id: "border-arr",
          type: "line",
          source: "arrondissements",
          paint: { "line-color": "#ffffff", "line-width": 1 }
        })

        map.on("click", "fill-arr", e => {
          const arr = e.features[0].properties.arrondissement
          setSelected(arr)
        })

        map.on("mouseenter", "fill-arr", () => {
          map.getCanvas().style.cursor = "pointer"
        })
        map.on("mouseleave", "fill-arr", () => {
          map.getCanvas().style.cursor = ""
        })
      }
    }

    if (map.isStyleLoaded()) {
      addLayers()
    } else {
      map.on("load", addLayers)
    }
  }, [contours, data, indicateur])

  return (
    <div style={{ flex: 1, position: "relative" }}>
      <div ref={mapRef} style={{ width: "100%", height: "100%" }} />
      <div style={{
        position: "absolute", bottom: 30, right: 10,
        background: "rgba(0,0,0,0.7)", padding: "10px",
        borderRadius: 8, fontSize: 12
      }}>
        <div style={{ marginBottom: 4 }}>{LABELS[indicateur]}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span>Min</span>
          <div style={{
            width: 100, height: 12, borderRadius: 4,
            background: "linear-gradient(to right, #1a237e, #f44336)"
          }} />
          <span>Max</span>
        </div>
      </div>
    </div>
  )
}