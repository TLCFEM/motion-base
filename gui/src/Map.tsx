import L, { LatLng } from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet/dist/images/layers.png";
import "leaflet/dist/images/layers-2x.png";
import markerRetina from "leaflet/dist/images/marker-icon-2x.png";
import marker from "leaflet/dist/images/marker-icon.png";
import shadow from "leaflet/dist/images/marker-shadow.png";
import earthquake from "./assets/earthquake.svg";

export function DefaultMap(container: string, centre: LatLng) {
    const map: L.Map = L.map(container).setView(centre, 6);

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 15,
        attribution: "OpenStreetMap",
    }).addTo(map);

    return map;
}

const LeafIcon = L.Icon.extend({
    options: {
        iconSize: [50, 50],
        iconAnchor: [25, 25],
        popupAnchor: [0, -20],
    },
});

// @ts-ignore
export const epicenterIcon = new LeafIcon({
    iconUrl: earthquake,
});

// @ts-ignore
export const stationIcon = L.icon({
    iconUrl: marker,
    iconRetinaUrl: markerRetina,
    shadowUrl: shadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    tooltipAnchor: [16, -28],
    shadowSize: [41, 41]
});
