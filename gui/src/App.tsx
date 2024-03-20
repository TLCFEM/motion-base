import { Component, createEffect, createSignal, onMount } from "solid-js";
import { jackpot, SeismicRecord } from "./API";
import { Card, CardContent, Paper, Typography } from "@suid/material";
import L, { LatLng, LatLngExpression } from "leaflet";

const [data, setData] = createSignal(new SeismicRecord({}));

jackpot().then((r) => setData(r));

interface ItemProps {
    label: string;
    value: string | number;
}

const MetadataItem = ({ label, value }: ItemProps) => {
    return (
        <>
            <Typography color="text.secondary" variant="subtitle2">
                {label}
            </Typography>
            <Typography variant="body2"> {value} </Typography>
        </>
    );
};
const [metadata, setMetadata] = createSignal<Array<ItemProps>>([]);

createEffect(() => {
    setMetadata([
        { label: "ID", value: data().id },
        { label: "File Name", value: data().file_name },
        { label: "Region", value: data().region.toUpperCase() },
        { label: "Magnitude", value: data().magnitude },
        { label: "PGA", value: data().maximum_acceleration },
        { label: "Event Time", value: data().event_time.toUTCString() },
    ]);
});

const MetadataCard: Component = () => {
    return (
        <Card sx={{ minWidth: 200, maxWidth: 400 }}>
            <CardContent>
                {metadata().map((item) => (
                    <MetadataItem label={item.label} value={item.value} />
                ))}
            </CardContent>
        </Card>
    );
};

const LeafIcon = L.Icon.extend({
    options: {
        iconSize: [38, 95],
        shadowSize: [50, 64],
        iconAnchor: [22, 94],
        shadowAnchor: [4, 62],
        popupAnchor: [-3, -76],
    },
});

export function DefaultMap(container: string, centre: LatLng) {
    const map: L.Map = L.map(container).setView(centre, 6);

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        // attribution: "© OpenStreetMap",
    }).addTo(map);
    return map;
}

// @ts-ignore
const greenIcon = new LeafIcon({
    iconUrl: "https://leafletjs.com/examples/custom-icons/leaf-green.png",
});
// @ts-ignore
const redIcon = new LeafIcon({
    iconUrl: "https://leafletjs.com/examples/custom-icons/leaf-red.png",
});
// @ts-ignore
const orangeIcon = new LeafIcon({
    iconUrl: "https://leafletjs.com/examples/custom-icons/leaf-orange.png",
});

const Epicenter: Component = () => {
    onMount(() => {
        const map = L.map("epicenter").setView([51.505, -0.09], 13);

        const tiles = L.tileLayer(
            "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                maxZoom: 19,
                attribution:
                    '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            },
        ).addTo(map);

        const marker = L.marker([51.5, -0.09]).addTo(map);

        const circle = L.circle([51.508, -0.11], {
            color: "red",
            fillColor: "#f03",
            fillOpacity: 0.5,
            radius: 500,
        }).addTo(map);

        const polygon = L.polygon([
            [51.509, -0.08],
            [51.503, -0.06],
            [51.51, -0.047],
        ]).addTo(map);
    });

    // let map: L.Map;
    // let event_marker: L.Marker;
    // let station_marker: L.Marker;

    onMount(() => {
        // const event_location = new LatLng(0, 0);
        // const station_location = new LatLng(0, 0);
        //
        // map = DefaultMap("epicenter", event_location);
        //
        // event_marker = L.marker(event_location, { icon: greenIcon }).addTo(map);
        // station_marker = L.marker(station_location, { icon: greenIcon }).addTo(
        //     map,
        // );
        //
        // event_marker.bindPopup("Event");
        // station_marker.bindPopup("Station");
    });

    // createEffect(() => {
    //     const metadata = data();
    //
    //     const event_location = new LatLng(
    //         metadata.event_location[1],
    //         metadata.event_location[0],
    //     );
    //     const station_location = new LatLng(
    //         metadata.station_location[1],
    //         metadata.station_location[0],
    //     );
    //     map.flyTo(event_location, 6);
    //
    //     event_marker.setLatLng(event_location);
    //     station_marker.setLatLng(station_location);
    // });

    return <Paper id="epicenter"></Paper>;
};

const App: Component = () => {
    return (
        <>
            <Epicenter />
            <MetadataCard />
        </>
    );
};

export default App;
