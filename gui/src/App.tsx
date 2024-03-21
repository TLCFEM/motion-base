import { Component, createEffect, createSignal, onMount } from "solid-js";
import { jackpot_waveform, SeismicRecord } from "./API";
import {
    AppBar,
    Box,
    Button,
    Card,
    CardActions,
    CardContent,
    Grid,
    Toolbar,
    Typography
} from "@suid/material";
import L, { LatLng } from "leaflet";
import "leaflet/dist/leaflet.css";
import { DefaultMap, epicenterIcon } from "./Map";
import Plotly from "plotly.js-dist-min";
import tippy from "tippy.js";
import "tippy.js/dist/tippy.css";
import "tippy.js/animations/scale.css";
import AboutModal from "./About";

const [data, setData] = createSignal(new SeismicRecord({}));
const [bounds, setBounds] = createSignal(L.latLngBounds(new LatLng(0, 0), new LatLng(0, 0)));

function load_once() {
    jackpot_waveform().then((r) => setData(r));
}

load_once();

interface ItemProps {
    tooltip?: string;
    label: string;
    value: string | number;
}

function distance_between(a: number[], b: number[]) {
    const event_location = new LatLng(a[1], a[0]);
    const station_location = new LatLng(b[1], b[0]);

    return event_location.distanceTo(station_location);
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
            { label: "Record Time", value: data().record_time.toUTCString() },
            {
                tooltip: "Distance between event and station locations over the delay between event and record times.",
                label: "Approximated Speed (km/s)",
                value: (distance_between(data().event_location, data().station_location) / (data().record_time.getTime() - data().event_time.getTime())).toFixed(2)
            }
        ]);
    });

    onMount(() => {
        tippy(`#btn-next`, {
            content: "Get another random record from the database.",
            animation: "scale",
            theme: "translucent"
        });
    });

    return <Card sx={{ border: "1px solid darkgrey", height: "90vh", display: "flex", flexDirection: "column" }}>
        <CardContent sx={{ flexGrow: 1 }}>
            {metadata().map((item) => (
                <>
                    <Typography color="text.secondary" variant="subtitle2"
                                id={item.label.toLowerCase().replace(new RegExp("[\s\(\)/]", "g"), "_")}>
                        {item.label}
                    </Typography>
                    <Typography variant="body2" sx={{ marginBottom: 1 }}>
                        {item.value}
                    </Typography>
                </>
            ))}
        </CardContent>
        <CardActions sx={{ justifyContent: "flex-end" }}>
            <Button id="btn-next" variant="contained" onClick={() => load_once()}>Next</Button>
        </CardActions>
    </Card>;
};

const Epicenter: Component = () => {
    let map: L.Map;
    let event_marker: L.Marker;
    let station_marker: L.Marker;

    onMount(() => {
        const event_location = new LatLng(13.4247317, 52.5068441);
        const station_location = new LatLng(13.4247317, 52.5068441);

        map = DefaultMap("epicenter", event_location);

        map.on("moveend", () => setBounds(map.getBounds()));

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

    return <Card sx={{ border: "1px solid darkgrey", height: "90vh" }}>
        <CardContent id="epicenter" sx={{ height: "100%" }} />
    </Card>;
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

    return <Card sx={{ border: "1px solid darkgrey", height: "90vh" }}>
        <CardContent id="canvas" sx={{ height: "100%" }} />
    </Card>;
};

const App: Component = () => {
    return <Box sx={{ marginLeft: "1vw", marginRight: "1vw", marginTop: "1vh" }}>
        <Grid container spacing={1}>
            <Grid item xs={12} md={12}>
                <AppBar position="static">
                    <Toolbar variant="dense" sx={{ justifyContent: "flex-end" }}>
                        <AboutModal />
                    </Toolbar>
                </AppBar>
            </Grid>
            <Grid item xs={12} md={2}>
                <MetadataCard />
            </Grid>
            <Grid item xs={12} md={5}>
                <Epicenter />
            </Grid>
            <Grid item xs={12} md={5}>
                <Waveform />
            </Grid>
        </Grid>
    </Box>;
};

export default App;
