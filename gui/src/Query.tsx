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

import { Component, createEffect, createSignal, For, onMount } from "solid-js";
import L, { LatLng } from "leaflet";
import { DefaultMap, epicenterIcon, stationIcon } from "./Map";
import {
    Alert,
    AlertTitle,
    Box,
    Button,
    ButtonGroup,
    Card,
    CardContent,
    Grid,
    LinearProgress,
    Modal,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TextField,
} from "@suid/material";
import { query_api, QueryConfig, SeismicRecord } from "./API";
import tippy from "tippy.js";
import "tippy.js/dist/tippy.css";
import "tippy.js/animations/scale.css";

const [eventLocation, setEventLocation] = createSignal<[number, number]>();
const [maxEventDistance, setMaxEventDistance] = createSignal(0);

const [records, setRecords] = createSignal([] as SeismicRecord[]);

const [error, setError] = createSignal("");

const Settings: Component = () => {
    const [loading, setLoading] = createSignal<boolean>(false);

    const [pageSize, setPageSize] = createSignal(0);
    const [pageNumber, setPageNumber] = createSignal(0);
    const [minMagnitude, setMinMagnitude] = createSignal(0);
    const [maxMagnitude, setMaxMagnitude] = createSignal(0);
    const [minPGA, setMinPGA] = createSignal(0);
    const [maxPGA, setMaxPGA] = createSignal(0);
    const [fromDate, setFromDate] = createSignal<Date>(new Date(0));
    const [toDate, setToDate] = createSignal<Date>(new Date(0));

    async function fetch() {
        setLoading(true);

        let config = new QueryConfig();
        if (pageSize() > 0) config.page_size = pageSize();
        if (pageNumber() > 0) config.page_number = pageNumber();
        if (minMagnitude() > 0) config.min_magnitude = minMagnitude();
        if (maxMagnitude() > 0) config.max_magnitude = maxMagnitude();
        if (minPGA() > 0) config.min_pga = minPGA();
        if (maxPGA() > 0) config.max_pga = maxPGA();
        if (fromDate().getTime() > 0) config.from_date = fromDate();
        if (toDate().getTime() > 0) config.to_date = toDate();
        if (eventLocation()) config.event_location = eventLocation();
        if (maxEventDistance() > 0) config.max_event_distance = maxEventDistance();

        try {
            setRecords(await query_api(config));
        } catch (e) {
            setRecords([]);
            setError((e as Error).message);
        }

        setLoading(false);
    }

    function clear() {
        setPageSize(0);
        setPageNumber(0);
        setMinMagnitude(0);
        setMaxMagnitude(0);
        setMinPGA(0);
        setMaxPGA(0);
        setFromDate(new Date(0));
        setToDate(new Date(0));

        // setRecords([] as SeismicRecord[]);
    }

    onMount(() => {
        tippy(`#btn-search`, {
            content: "Search for records.",
            animation: "scale",
        });
        tippy(`#btn-clear`, {
            content: "Clear searching criteria.",
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
                    alignItems: "center",
                    gap: "1rem",
                }}
            >
                <TextField
                    label="Page Number"
                    type="number"
                    value={pageNumber()}
                    defaultValue={pageNumber()}
                    onChange={(_, value) => setPageNumber(Math.max(Number(value), 0))}
                    disabled={loading()}
                />
                <TextField
                    label="Page Size"
                    type="number"
                    value={pageSize() > 0 ? pageSize() : ""}
                    defaultValue={pageSize() > 0 ? pageSize() : ""}
                    onChange={(_, value) => setPageSize(value ? Math.max(Math.min(1000, Number(value)), 1) : 0)}
                    disabled={loading()}
                />
                <TextField
                    label="Min Magnitude"
                    type="number"
                    value={minMagnitude() > 0 ? minMagnitude() : ""}
                    defaultValue={minMagnitude() > 0 ? minMagnitude() : ""}
                    onChange={(_, value) => setMinMagnitude(value ? Math.max(Math.min(10, Number(value)), 0) : 0)}
                    disabled={loading()}
                />
                <TextField
                    label="Max Magnitude"
                    type="number"
                    value={maxMagnitude() > 0 ? maxMagnitude() : ""}
                    defaultValue={maxMagnitude() > 0 ? maxMagnitude() : ""}
                    onChange={(_, value) => setMaxMagnitude(value ? Math.max(Math.min(10, Number(value)), 0) : 0)}
                    disabled={loading()}
                />
                <TextField
                    label="Min PGA (Gal)"
                    type="number"
                    value={minPGA() > 0 ? minPGA() : ""}
                    defaultValue={minPGA() > 0 ? minPGA() : ""}
                    onChange={(_, value) => setMinPGA(value ? Number(value) : 0)}
                    disabled={loading()}
                />
                <TextField
                    label="Max PGA (Gal)"
                    type="number"
                    value={maxPGA() > 0 ? maxPGA() : ""}
                    defaultValue={maxPGA() > 0 ? maxPGA() : ""}
                    onChange={(_, value) => setMaxPGA(value ? Number(value) : 0)}
                    disabled={loading()}
                />
                <TextField
                    label="From"
                    type="date"
                    InputLabelProps={{ shrink: true }}
                    value={fromDate().getTime() === 0 ? "" : fromDate().toISOString().split("T")[0]}
                    onChange={(_, value) => setFromDate(value ? new Date(Date.parse(value)) : new Date(0))}
                    sx={{ width: "16ch" }}
                    disabled={loading()}
                />
                <TextField
                    label="To"
                    type="date"
                    InputLabelProps={{ shrink: true }}
                    value={toDate().getTime() === 0 ? "" : toDate().toISOString().split("T")[0]}
                    onChange={(_, value) => setToDate(value ? new Date(Date.parse(value)) : new Date(0))}
                    sx={{ width: "16ch" }}
                    disabled={loading()}
                />
                <ButtonGroup variant="outlined">
                    <Button onClick={fetch} id="btn-search" disabled={loading()}>
                        Search
                    </Button>
                    <Button onClick={clear} id="btn-clear" disabled={loading()}>
                        Clear
                    </Button>
                </ButtonGroup>
                <Modal open={error() !== ""} onClose={() => setError("")}>
                    <Alert
                        severity="error"
                        sx={{
                            position: "absolute",
                            top: "50%",
                            left: "50%",
                            transform: "translate(-50%, -50%)",
                            width: "40%",
                        }}
                    >
                        <AlertTitle>Error</AlertTitle>
                        {error()}
                    </Alert>
                </Modal>
            </CardContent>
            <Box sx={{ width: "100%" }}>
                {loading() ? <LinearProgress /> : <LinearProgress variant="determinate" value={0} />}
            </Box>
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
                            <TableCell align="right">PGA (Gal, cm/s^2)</TableCell>
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
                                    <TableCell align="right">{row.magnitude}</TableCell>
                                    <TableCell align="right">{Math.abs(row.maximum_acceleration).toFixed(2)}</TableCell>
                                    <TableCell align="right">{row.depth}</TableCell>
                                    <TableCell align="right">{row.duration}</TableCell>
                                    <TableCell align="right">{row.event_time.toUTCString()}</TableCell>
                                    <TableCell align="right">{row.station_code.toUpperCase()}</TableCell>
                                </TableRow>
                            )}
                        </For>
                    </TableBody>
                </Table>
            </TableContainer>
        </Card>
    );
};

const QueryDatabase: Component = () => {
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

        setEventLocation([normalize_longitude(map.getCenter().lng), normalize_latitude(map.getCenter().lat)]);
        setMaxEventDistance(bound.getNorthEast().distanceTo(bound.getSouthWest()) / 2);
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

                marker?.bindPopup(`${marker?.getPopup()?.getContent()}</br>${record.id}`);
            } else {
                const marker = L.marker(new LatLng(record.station_location[1], record.station_location[0]), {
                    icon: stationIcon,
                }).addTo(map);

                marker.bindPopup(record.id);
                station_map.set(key, marker);
            }

            key = record.event_location[0] * record.event_location[1];

            if (event_map.has(key)) {
                const marker = event_map.get(key);

                marker?.bindPopup(`${marker?.getPopup()?.getContent()}</br>${record.id}`);
            } else {
                const marker = L.marker(new LatLng(record.event_location[1], record.event_location[0]), {
                    icon: epicenterIcon,
                }).addTo(map);

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

export default QueryDatabase;
