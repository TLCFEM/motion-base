import L, { LatLng } from "leaflet";
import earthquake from "./assets/earthquake.svg";

export function DefaultMap(container: string, centre: LatLng) {
    const map: L.Map = L.map(container).setView(centre, 6);

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 15,
        attribution: "OpenStreetMap"
    }).addTo(map);

    return map;
}


const LeafIcon = L.Icon.extend({
    options: {
        iconSize: [50, 50],
        iconAnchor: [25, 25],
        popupAnchor: [0, -20]
    }
});

// @ts-ignore
export const epicenterIcon = new LeafIcon({
    iconUrl: earthquake
});

