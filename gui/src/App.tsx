import { Component, createEffect, createSignal, onMount } from "solid-js";
import { jackpot, SeismicRecord } from "./API";
import { Button, Card, CardContent, Paper, Typography } from "@suid/material";
import L, { LatLng } from "leaflet";
import earthquake from "./assets/earthquake.svg";

const [data, setData] = createSignal(new SeismicRecord({}));

function load_once() { // load on
    // e
    jackpot().then((r) => setData(r));
}

load_once();

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

export function DefaultMap(container: string, centre: LatLng) {
    const map: L.Map = L.map(container).setView(centre, 6);

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "© OpenStreetMap"
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
const epicenterIcon = new LeafIcon({
    iconUrl: earthquake
});

const Epicenter: Component = () => {
    let map: L.Map;
    let event_marker: L.Marker;
    let station_marker: L.Marker;

    onMount(() => {
        const event_location = new LatLng(13.4247317, 52.5068441);
        const station_location = new LatLng(13.4247317, 52.5068441);

        map = DefaultMap("epicenter", event_location);

        event_marker = L.marker(event_location, { icon: epicenterIcon }).addTo(map);
        station_marker = L.marker(station_location).addTo(map);
    });

    createEffect(() => {
        const current_record = data();

        const event_location = new LatLng(
            current_record.event_location[1],
            current_record.event_location[0]
        );
        const station_location = new LatLng(
            current_record.station_location[1],
            current_record.station_location[0]
        );
        map.flyTo(event_location, 6);

        event_marker.setLatLng(event_location);
        station_marker.setLatLng(station_location);

        event_marker.bindPopup("Event Location: " + event_marker.getLatLng().toString());
        station_marker.bindPopup("Station Location: " + station_marker.getLatLng().toString());
    });

    return <Card id="epicenter" />;
};

const App: Component = () => {
    return (
        <>
            <MetadataCard />
            <Button onClick={() => load_once()}>Reload</Button>
            <Epicenter />
        </>
    );
};

export default App;
