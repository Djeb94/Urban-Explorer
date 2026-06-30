import { useEffect, useRef, useState } from "react"
import maplibregl from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import api from "./api"

const LABELS = {
  accessibilite_achat: "Accessibilité à l'achat",
  score_vivabilite:    "Vivabilité urbaine",
  score_attractivite:  "Score attractivité",
  mixite_sociale:      "Mixité sociale",
  total_delits:            "Criminalité",
  total_logements_sociaux: "Logements sociaux",
  surface_totale_m2:       "Espaces verts (m²)",
  nb_stations:             "Stations RATP"
}

const COUCHE_LABELS = {
  criminalite:       "total_delits",
  logements_sociaux: "total_logements_sociaux",
  espaces_verts:     "surface_totale_m2",
  stations:          "nb_stations"
}

export default function Map({ data, selected, compared, setSelected, indicateur, activeCouche, coucheData }) {
  const mapRef = useRef(null)
  const mapInstance = useRef(null)
  const popupRef = useRef(null)
  const [contours, setContours] = useState(null)
  const [mapReady, setMapReady] = useState(false)
  const indicateurRef = useRef(indicateur)
  const setSelectedRef = useRef(setSelected)
  const activeCoucheRef = useRef(activeCouche)

  useEffect(() => { indicateurRef.current = indicateur }, [indicateur])
  useEffect(() => { setSelectedRef.current = setSelected }, [setSelected])
  useEffect(() => { activeCoucheRef.current = activeCouche }, [activeCouche])

  useEffect(() => {
    api.get(`/contours`).then(res => setContours(res.data))
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
    popupRef.current = new maplibregl.Popup({ closeButton: false, closeOnClick: false })
    mapInstance.current.on("load", () => setMapReady(true))
    return () => mapInstance.current.remove()
  }, [])

  // ── Couche choroplèthe principale ──────────────────────────────
  useEffect(() => {
    if (!mapInstance.current || !contours || data.length === 0) return
    const map = mapInstance.current

    const addLayers = () => {
      const values = data.map(d => d[indicateur]).filter(v => v !== null && v !== undefined)
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

      if (map.getLayer("fill-arr"))         map.removeLayer("fill-arr")
      if (map.getLayer("border-arr"))       map.removeLayer("border-arr")
      if (map.getSource("arrondissements")) map.removeSource("arrondissements")

      map.addSource("arrondissements", { type: "geojson", data: geojson })

      map.addLayer({
        id: "fill-arr",
        type: "fill",
        source: "arrondissements",
        paint: {
          "fill-color": [
            "interpolate", ["linear"], ["get", "value"],
            min, "#ef4444",
            (min + max) / 2, "#f59e0b",
            max, "#22c55e"
          ],
          "fill-opacity": activeCouche ? 0 : 0.7
        }
      })

      map.addLayer({
        id: "border-arr",
        type: "line",
        source: "arrondissements",
        paint: { "line-color": "#ffffff", "line-width": 1 }
      })

      map.off("click", "fill-arr")
      map.off("mousemove", "fill-arr")
      map.off("mouseleave", "fill-arr")

      map.on("click", "fill-arr", e => {
        const arr = e.features[0].properties.arrondissement
        setSelectedRef.current(arr)
      })

      map.on("mousemove", "fill-arr", e => {
        map.getCanvas().style.cursor = "pointer"
        const arr = e.features[0].properties.arrondissement
        const val = e.features[0].properties.value
        popupRef.current
          .setLngLat(e.lngLat)
          .setHTML(`
            <div style="background:#161b27;padding:8px 12px;border-radius:6px;color:white;font-size:13px;border:1px solid #3b82f6">
              <b>${arr}ème arrondissement</b><br/>
              <span style="color:#60a5fa">${LABELS[indicateurRef.current]} : ${Number(val).toFixed(2)}</span>
            </div>
          `)
          .addTo(map)
      })

      map.on("mouseleave", "fill-arr", () => {
        map.getCanvas().style.cursor = ""
        popupRef.current.remove()
      })
    }

    if (map.isStyleLoaded()) addLayers()
    else map.on("load", addLayers)

  }, [contours, data, indicateur, activeCouche])

  // ── Couche superposée ──────────────────────────────────────────
  useEffect(() => {
    const map = mapInstance.current
    if (!map || !mapReady) return

    // Nettoyage
    map.off("mousemove", "couche-fill")
    map.off("mouseleave", "couche-fill")
    map.off("click", "couche-fill")
    if (map.getLayer("couche-fill"))    map.removeLayer("couche-fill")
    if (map.getSource("couche-data"))   map.removeSource("couche-data")

    if (!activeCouche || coucheData.length === 0 || !contours) return

    const geojson = {
      type: "FeatureCollection",
      features: contours.features.map(f => {
        const arr = f.properties.c_ar
        const row = coucheData.find(d => Math.round(d.arrondissement) === arr)
        const valKey = COUCHE_LABELS[activeCouche]
        return {
          ...f,
          properties: {
            ...f.properties,
            couche_value: row && valKey ? row[valKey] : 0
          }
        }
      })
    }

    const vals = geojson.features.map(f => f.properties.couche_value).filter(Boolean)
    const min = Math.min(...vals)
    const max = Math.max(...vals)

    map.addSource("couche-data", { type: "geojson", data: geojson })
    map.addLayer({
      id: "couche-fill",
      type: "fill",
      source: "couche-data",
      paint: {
        "fill-color": [
          "interpolate", ["linear"], ["get", "couche_value"],
          min, "#ef4444",
          (min + max) / 2, "#f59e0b",
          max, "#22c55e"
        ],
        "fill-opacity": 0.7
      }
    })

    // Hover sur couche
    map.on("mousemove", "couche-fill", e => {
      map.getCanvas().style.cursor = "pointer"
      const arr = e.features[0].properties.c_ar
      const val = e.features[0].properties.couche_value
      popupRef.current
        .setLngLat(e.lngLat)
        .setHTML(`
          <div style="background:#161b27;padding:8px 12px;border-radius:6px;color:white;font-size:13px;border:1px solid #3b82f6">
            <b>${arr}ème arrondissement</b><br/>
            <span style="color:#60a5fa">${LABELS[COUCHE_LABELS[activeCoucheRef.current]]} : ${Number(val).toLocaleString("fr-FR")}</span>
          </div>
        `)
        .addTo(map)
    })

    map.on("mouseleave", "couche-fill", () => {
      map.getCanvas().style.cursor = ""
      popupRef.current.remove()
    })

    map.on("click", "couche-fill", e => {
      const arr = e.features[0].properties.c_ar
      setSelectedRef.current(arr)
    })

  }, [activeCouche, coucheData, contours, mapReady])

  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      <div ref={mapRef} style={{ width: "100%", height: "100%" }} />
      <div style={{
        position: "absolute", bottom: 10, right: 10,
        background: "rgba(0,0,0,0.7)", padding: "10px",
        borderRadius: 8, fontSize: 12
      }}>
        <div style={{ marginBottom: 4 }}>
          {LABELS[activeCouche ? COUCHE_LABELS[activeCouche] : indicateur] || ""}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span>Min</span>
          <div style={{
            width: 100, height: 12, borderRadius: 4,
            background: "linear-gradient(to right, #ef4444, #f59e0b, #22c55e)"
          }} />
          <span>Max</span>
        </div>
      </div>
    </div>
  )
}