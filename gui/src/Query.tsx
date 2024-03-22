import { Component, createEffect, createSignal, For, onMount } from "solid-js";
import L, { LatLng } from "leaflet";
import { DefaultMap, epicenterIcon, stationIcon } from "./Map";
import {
    Button,
    Card,
    CardContent,
    Grid,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TextField,
} from "@suid/material";
import { query, QueryConfig, SeismicRecord } from "./API";
import tippy from "tippy.js";
import "tippy.js/dist/tippy.css";
import "tippy.js/animations/scale.css";

const [config, setConfig] = createSignal<QueryConfig>(new QueryConfig());
const [records, setRecords] = createSignal<SeismicRecord[]>(
    [] as SeismicRecord[],
);

async function fetch() {
    setRecords(await query(config()));
}

const Settings: Component = () => {
    const [from, setFrom] = createSignal<string>("");
    const [to, setTo] = createSignal<string>("");

    onMount(() => {
        tippy(`#btn-search`, {
            content: "Search for records.",
            animation: "scale",
        });
    });

    return (
        <Card>
            <CardContent
                sx={{
                    display: "flex",
                    flexDirection: "row",
                    justifyContent: "center",
                    alignContent: "center",
                    gap: "1rem",
                }}
            >
                <TextField
                    label="Page Size"
                    type="number"
                    value={config().page_size}
                    onChange={(_, value) =>
                        setConfig({
                            ...config(),
                            page_size: value ? Number(value) : undefined,
                        })
                    }
                />
                <TextField
                    label="Min Magnitude"
                    type="number"
                    value={config().min_magnitude}
                    onChange={(_, value) =>
                        setConfig({
                            ...config(),
                            min_magnitude: value ? Number(value) : undefined,
                        })
                    }
                />
                <TextField
                    label="Max Magnitude"
                    type="number"
                    value={config().max_magnitude}
                    onChange={(_, value) =>
                        setConfig({
                            ...config(),
                            max_magnitude: value ? Number(value) : undefined,
                        })
                    }
                />
                <TextField
                    label="Min PGA (Gal)"
                    type="number"
                    value={config().min_pga}
                    onChange={(_, value) =>
                        setConfig({
                            ...config(),
                            min_pga: value ? Number(value) : undefined,
                        })
                    }
                />
                <TextField
                    label="Max PGA (Gal)"
                    type="number"
                    value={config().max_pga}
                    onChange={(_, value) =>
                        setConfig({
                            ...config(),
                            max_pga: value ? Number(value) : undefined,
                        })
                    }
                />
                <TextField
                    label="From"
                    type="date"
                    InputLabelProps={{ shrink: true }}
                    value={from()}
                    onChange={(_, value) => {
                        setFrom(value);
                        setConfig({
                            ...config(),
                            from_date: value
                                ? new Date(Date.parse(value))
                                : undefined,
                        });
                    }}
                />
                <TextField
                    label="To"
                    type="date"
                    InputLabelProps={{ shrink: true }}
                    value={to()}
                    onChange={(_, value) => {
                        setTo(value);
                        setConfig({
                            ...config(),
                            to_date: value
                                ? new Date(Date.parse(value))
                                : undefined,
                        });
                    }}
                />
                <Button onClick={fetch} id="btn-search" variant="contained">
                    Search
                </Button>
            </CardContent>
        </Card>
    );
};

const BasicTable: Component = () => {
    return (
        <Card sx={{ border: "1px solid darkgrey", height: "80vh" }}>
            <TableContainer sx={{ maxHeight: "100%", overflow: "auto" }}>
                <Table stickyHeader>
                    <TableHead>
                        <TableRow>
                            <TableCell>ID</TableCell>
                            <TableCell>File Name</TableCell>
                            <TableCell align="right">Magnitude</TableCell>
                            <TableCell align="right">
                                PGA (Gal, cm/s^2)
                            </TableCell>
                            <TableCell align="right">Depth (km)</TableCell>
                            <TableCell align="right">Duration (s)</TableCell>
                            <TableCell align="right">Event Time</TableCell>
                            <TableCell align="right">Station</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        <For each={records()}>
                            {(row) => (
                                <TableRow
                                    sx={{
                                        "&:last-child td, &:last-child th": {
                                            border: 0,
                                        },
                                    }}
                                >
                                    <TableCell component="th" scope="row">
                                        {row.id}
                                    </TableCell>
                                    <TableCell>{row.file_name}</TableCell>
                                    <TableCell align="right">
                                        {row.magnitude}
                                    </TableCell>
                                    <TableCell align="right">
                                        {row.maximum_acceleration}
                                    </TableCell>
                                    <TableCell align="right">
                                        {row.depth}
                                    </TableCell>
                                    <TableCell align="right">
                                        {row.duration}
                                    </TableCell>
                                    <TableCell align="right">
                                        {row.event_time.toUTCString()}
                                    </TableCell>
                                    <TableCell align="right">
                                        {row.station_code.toUpperCase()}
                                    </TableCell>
                                </TableRow>
                            )}
                        </For>
                    </TableBody>
                </Table>
            </TableContainer>
        </Card>
    );
};

const Overview: Component = () => {
    let map: L.Map;

    const normalize_longitude = (lon: number) => {
        while (lon < -180) {
            lon += 360;
        }
        while (lon > 180) {
            lon -= 360;
        }
        return lon;
    };

    const normalize_latitude = (lat: number) => {
        while (lat < -90) {
            lat += 180;
        }
        while (lat > 90) {
            lat -= 180;
        }
        return lat;
    };

    const update_location = () => {
        const bound = map.getBounds();
        setConfig({
            ...config(),
            event_location: [
                normalize_longitude(map.getCenter().lng),
                normalize_latitude(map.getCenter().lat),
            ],
            max_event_distance:
                bound.getNorthEast().distanceTo(bound.getSouthWest()) / 2,
        });
    };

    onMount(() => {
        map = DefaultMap("overview", new LatLng(35.652832, 139.839478));

        update_location();

        map.on("moveend", update_location);
    });

    let station_map = new Map<number, L.Marker>();
    let event_map = new Map<number, L.Marker>();

    createEffect(() => {
        for (const marker of station_map.values()) marker.remove();
        station_map.clear();
        for (const marker of event_map.values()) marker.remove();
        event_map.clear();

        for (const record of records()) {
            let key = record.station_location[0] * record.station_location[1];

            if (station_map.has(key)) {
                const marker = station_map.get(key);

                marker?.bindPopup(
                    `${marker?.getPopup()?.getContent()}</br>${record.id}`,
                );
            } else {
                const marker = L.marker(
                    new LatLng(
                        record.station_location[1],
                        record.station_location[0],
                    ),
                    { icon: stationIcon },
                ).addTo(map);

                marker.bindPopup(record.id);
                station_map.set(key, marker);
            }

            key = record.event_location[0] * record.event_location[1];

            if (event_map.has(key)) {
                const marker = event_map.get(key);

                marker?.bindPopup(
                    `${marker?.getPopup()?.getContent()}</br>${record.id}`,
                );
            } else {
                const marker = L.marker(
                    new LatLng(
                        record.event_location[1],
                        record.event_location[0],
                    ),
                    { icon: epicenterIcon },
                ).addTo(map);

                marker.bindPopup(record.id);
                event_map.set(key, marker);
            }
        }
    });

    return (
        <>
            <Grid item xs={12} md={12}>
                <Settings />
            </Grid>
            <Grid item xs={12} md={5}>
                <Card sx={{ border: "1px solid darkgrey", height: "80vh" }}>
                    <CardContent id="overview" sx={{ height: "100%" }} />
                </Card>
            </Grid>
            <Grid item xs={12} md={7}>
                <BasicTable />
            </Grid>
        </>
    );
};

export default Overview;
