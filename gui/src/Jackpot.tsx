//  Copyright (C) 2022-2024 Theodore Chang
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import {
    Component,
    createEffect,
    createMemo,
    createResource,
    onMount,
} from "solid-js";
import { jackpot_waveform_api } from "./API";
import {
    Box,
    Button,
    Card,
    CardActions,
    CardContent,
    Grid,
    LinearProgress,
    Typography,
} from "@suid/material";
import L, { LatLng } from "leaflet";
import { DefaultMap, epicenterIcon, stationIcon } from "./Map";
import Plotly from "plotly.js-dist-min";
import tippy from "tippy.js";
import "tippy.js/dist/tippy.css";
import "tippy.js/animations/scale.css";

const [data, { refetch }] = createResource(jackpot_waveform_api);

function distance_between(a: number[], b: number[]) {
    const event_location = new LatLng(a[1], a[0]);
    const station_location = new LatLng(b[1], b[0]);

    return event_location.distanceTo(station_location);
}

const MetadataCard: Component = () => {
    const metadata = createMemo(() => [
        { label: "ID", value: data.loading ? "---" : data().id },
        { label: "File Name", value: data.loading ? "---" : data().file_name },
        {
            label: "Region",
            value: data.loading ? "---" : data().region.toUpperCase(),
        },
        {
            label: "Category",
            value: data.loading ? "---" : data().category.toUpperCase(),
        },
        { label: "Magnitude", value: data.loading ? "---" : data().magnitude },
        { label: "Depth (km)", value: data.loading ? "---" : data().depth },
        {
            label: "PGA (Gal, cm/s^2)",
            value: data.loading
                ? "---"
                : Math.abs(data().maximum_acceleration).toFixed(2),
        },
        {
            label: `Sampling Frequency (${data.loading ? "---" : data().sampling_frequency_unit})`,
            value: data.loading ? "---" : data().sampling_frequency,
        },
        {
            label: "Event Time",
            value: data.loading ? "---" : data().event_time.toUTCString(),
        },
        {
            label: "Record Time",
            value: data.loading
                ? "---"
                : data().record_time.getTime() > 0
                  ? data().record_time.toUTCString()
                  : "---",
        },
        {
            tooltip:
                "Distance between event and station locations over the delay between event and record times.",
            label: "Approximated Speed (km/s)",
            value: data.loading
                ? "---"
                : data().record_time.getTime() > 0
                  ? (
                        distance_between(
                            data().event_location,
                            data().station_location,
                        ) /
                        (data().record_time.getTime() -
                            data().event_time.getTime())
                    ).toFixed(2)
                  : "---",
        },
    ]);

    onMount(() => {
        tippy(`#btn-next`, {
            content: "Get another random record from the database.",
            animation: "scale",
            theme: "translucent",
        });
    });

    return (
        <Card
            sx={{
                border: "1px solid darkgrey",
                height: "90vh",
                display: "flex",
                flexDirection: "column",
            }}
        >
            <CardContent sx={{ flexGrow: 1 }}>
                {metadata().map((item) => (
                    <>
                        <Typography
                            color="text.secondary"
                            variant="subtitle2"
                            id={item.label
                                .toLowerCase()
                                .replace(new RegExp("[s()/]", "g"), "_")}
                        >
                            {item.label}
                        </Typography>
                        <Typography variant="body2" sx={{ marginBottom: 1 }}>
                            {item.value}
                        </Typography>
                    </>
                ))}
            </CardContent>
            <Box sx={{ width: "100%" }}>
                {data.loading ? (
                    <LinearProgress />
                ) : (
                    <LinearProgress variant="determinate" value={0} />
                )}
            </Box>
            <CardActions sx={{ justifyContent: "flex-end" }}>
                <Button
                    id="btn-next"
                    variant="contained"
                    onClick={refetch}
                    disabled={data.loading}
                >
                    Next
                </Button>
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
            map,
        );
        station_marker = L.marker(station_location, {
            icon: stationIcon,
        }).addTo(map);
    });

    createEffect(() => {
        if (data.loading) return;

        const event_location = new LatLng(
            data().event_location[1],
            data().event_location[0],
        );
        const station_location = new LatLng(
            data().station_location[1],
            data().station_location[0],
        );
        map.flyTo(event_location, 6);

        event_marker.setLatLng(event_location);
        station_marker.setLatLng(station_location);

        event_marker.bindPopup(
            "Event Location: " + event_marker.getLatLng().toString(),
        );
        station_marker.bindPopup(
            "Station Location: " + station_marker.getLatLng().toString(),
        );
    });

    return (
        <Card sx={{ border: "1px solid darkgrey", height: "90vh" }}>
            <CardContent id="epicenter" sx={{ height: "100%" }} />
        </Card>
    );
};

const Waveform: Component = () => {
    createEffect(async () => {
        if (data.loading) return;

        await Plotly.newPlot(
            "canvas",
            [
                {
                    x: Array<number>(data().waveform.length)
                        .fill(0)
                        .map((_, i) => i * data().time_interval),
                    y: data().waveform,
                    type: "scatter",
                    mode: "lines",
                    name: data().id,
                },
            ],
            {
                title: data().file_name,
                xaxis: {
                    title: "Time (s)",
                    autorange: true,
                    automargin: true,
                },
                yaxis: {
                    title: "Acceleration (cm/s^2)",
                    autorange: true,
                    automargin: true,
                },
                autosize: true,
            },
            { autosizable: true, responsive: true },
        );
    });

    return (
        <Card sx={{ border: "1px solid darkgrey", height: "90vh" }}>
            <CardContent id="canvas" sx={{ height: "100%" }} />
        </Card>
    );
};

const Jackpot: Component = () => {
    onMount(refetch);

    return (
        <>
            <Grid item xs={12} md={2}>
                <MetadataCard />
            </Grid>
            <Grid item xs={12} md={5}>
                <Epicenter />
            </Grid>
            <Grid item xs={12} md={5}>
                <Waveform />
            </Grid>
        </>
    );
};

export default Jackpot;
