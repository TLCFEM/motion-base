import { Component, createEffect, createSignal, onMount } from "solid-js";
import L, { LatLng } from "leaflet";
import { DefaultMap } from "./Map";
import { Button, Card, CardContent, Grid } from "@suid/material";
import { query, QueryConfig, SeismicRecord } from "./API";

const [config, setConfig] = createSignal<QueryConfig>(new QueryConfig());
const [records, setRecords] = createSignal<SeismicRecord[]>(
    [] as SeismicRecord[],
);

async function fetch() {
    setRecords(await query(config()));
}

const Settings: Component = () => {
    return (
        <Grid item xs={12} md={12}>
            <Card>
                <CardContent>
                    <Button onClick={fetch}>Show</Button>
                </CardContent>
            </Card>
        </Grid>
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
        map = DefaultMap("overview", new LatLng(13.4247317, 52.5068441));

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
            <Settings />
            <Grid item xs={12} md={8}>
                <Card sx={{ border: "1px solid darkgrey", height: "90vh" }}>
                    <CardContent id="overview" sx={{ height: "100%" }} />
                </Card>
            </Grid>
        </>
    );
};

export default Overview;
