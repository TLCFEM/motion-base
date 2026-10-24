//  Copyright (C) 2022-2026 Theodore Chang
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.

import L, { LatLng } from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet/dist/images/layers.png";
import "leaflet/dist/images/layers-2x.png";
import markerRetina from "leaflet/dist/images/marker-icon-2x.png";
import marker from "leaflet/dist/images/marker-icon.png";
import markerRetina2 from "./assets/marker-icon2-2x.png";
import marker2 from "./assets/marker-icon2.png";
import shadow from "leaflet/dist/images/marker-shadow.png";
import earthquake from "./assets/earthquake.svg";

export function DefaultMap(container: string, centre: LatLng, zoom = 6) {
    const map = L.map(container).setView(centre, zoom);

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
}) as unknown as typeof L.Icon;

export const epicenterIcon = new LeafIcon({ iconUrl: earthquake });

export const stationIcon = L.icon({
    iconUrl: marker,
    iconRetinaUrl: markerRetina,
    shadowUrl: shadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    tooltipAnchor: [16, -28],
    shadowSize: [41, 41],
});

export const selectedStationIcon = L.icon({
    iconUrl: marker2,
    iconRetinaUrl: markerRetina2,
    shadowUrl: shadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    tooltipAnchor: [16, -28],
    shadowSize: [41, 41],
});
