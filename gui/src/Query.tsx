import { Component, createEffect, createSignal, For, onMount } from "solid-js";
import L, { LatLng } from "leaflet";
import { DefaultMap } from "./Map";
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
                    label="Min PGA"
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
                    label="Max PGA"
                    type="number"
                    value={config().max_pga}
                    onChange={(_, value) =>
                        setConfig({
                            ...config(),
                            max_pga: value ? Number(value) : undefined,
                        })
                    }
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
            <TableContainer>
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

    let laglon_map = new Map<number, L.Marker>();

    createEffect(() => {
        for (const marker of laglon_map.values()) marker.remove();
        laglon_map.clear();

        for (const record of records()) {
            const key = record.station_location[0] * record.station_location[1];

            if (laglon_map.has(key)) {
                const marker = laglon_map.get(key);

                marker?.bindPopup(
                    `${marker?.getPopup()?.getContent()}</br>${record.id}`,
                );
            } else {
                const marker = L.marker(
                    new LatLng(
                        record.station_location[1],
                        record.station_location[0],
                    ),
                ).addTo(map);

                marker.bindPopup(record.id);
                laglon_map.set(key, marker);
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
