import { Component, createEffect, createSignal, onMount } from "solid-js";
import { jackpot_waveform, SeismicRecord } from "./API";
import { Box, Button, Card, CardActions, CardContent, Grid, Typography } from "@suid/material";
import L, { LatLng } from "leaflet";
import "leaflet/dist/leaflet.css";
import { DefaultMap, epicenterIcon } from "./Map";
import Plotly from "plotly.js-dist-min";

const [data, setData] = createSignal(new SeismicRecord({}));

function load_once() {
    jackpot_waveform().then((r) => setData(r));
}

load_once();

interface ItemProps {
    label: string;
    value: string | number;
}

const MetadataCard: Component = () => {
    const [metadata, setMetadata] = createSignal<Array<ItemProps>>([]);

    createEffect(() => {
        setMetadata([
            { label: "ID", value: data().id },
            { label: "File Name", value: data().file_name },
            { label: "Region", value: data().region.toUpperCase() },
            { label: "Category", value: data().category.toUpperCase() },
            { label: "Magnitude", value: data().magnitude },
            { label: "Depth (km)", value: data().depth },
            { label: "PGA (Gal, cm/s^2)", value: data().maximum_acceleration },
            { label: `Sampling Frequency (${data().sampling_frequency_unit})`, value: data().sampling_frequency },
            { label: "Event Time", value: data().event_time.toUTCString() },
            { label: "Record Time", value: data().record_time.toUTCString() }
        ]);
    });

    return (
        <Card>
            <CardContent>
                {metadata().map((item) => (
                    <>
                        <Typography color="text.secondary" variant="subtitle2">
                            {item.label}
                        </Typography>
                        <Typography variant="body2" sx={{ marginBottom: 1 }}>
                            {item.value}
                        </Typography>
                    </>
                ))}
            </CardContent>
            <CardActions sx={{ justifyContent: "flex-end" }}>
                <Button variant="contained" onClick={() => load_once()}>Next</Button>
            </CardActions>
        </Card>
    );
};

const Epicenter: Component = () => {
    let map: L.Map;
    let event_marker: L.Marker;
    let station_marker: L.Marker;

    onMount(() => {
        const event_location = new LatLng(13.4247317, 52.5068441);
        const station_location = new LatLng(13.4247317, 52.5068441);

        map = DefaultMap("epicenter", event_location);

        event_marker = L.marker(event_location, { icon: epicenterIcon }).addTo(
            map
        );
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

        event_marker.bindPopup(
            "Event Location: " + event_marker.getLatLng().toString()
        );
        station_marker.bindPopup(
            "Station Location: " + station_marker.getLatLng().toString()
        );
    });

    return <Card id="epicenter" sx={{ height: 500 }} />;
};

const Waveform: Component = () => {
    createEffect(() => {
        const record = data();

        Plotly.newPlot(
            "canvas",
            [
                {
                    x: Array<number>(record.waveform.length)
                        .fill(0)
                        .map((_, i) => i * record.time_interval),
                    y: record.waveform,
                    type: "scatter",
                    mode: "lines",
                    name: record.id
                }
            ],
            {
                title: record.file_name,
                xaxis: {
                    title: "Time (s)",
                    autorange: true,
                    automargin: true
                },
                yaxis: {
                    title: "Acceleration (cm/s^2)",
                    autorange: true,
                    automargin: true
                },
                autosize: true
            }, { autosizable: true, responsive: true }
        ).then();
    });

    return <Card id="canvas" sx={{ height: 500 }}></Card>;
};

const App: Component = () => {
    return <Box sx={{ marginLeft: 4, marginRight: 4, marginTop: 4 }}>
        <Grid container spacing={1}>
            <Grid item xs={12} md={12}>
                <MetadataCard />
            </Grid>
            <Grid item xs={12} md={12}>
                <Epicenter />
            </Grid>
            <Grid item xs={12} md={12}>
                <Waveform />
            </Grid>
        </Grid>
    </Box>;
};

export default App;
