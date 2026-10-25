//  Copyright (C) 2022-2026 Theodore Chang
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.

import { Component, createEffect, createResource, createSignal, For, onCleanup, onMount } from "solid-js";
import L, { LatLng } from "leaflet";
import Plotly from "plotly.js-basic-dist-min";
import { jackpot_waveform_api, SeismicRecord, toUTC } from "./api";
import { DefaultMap, epicenterIcon, stationIcon, toLatLng } from "./Map";
import { plotAxis, plotConfig, plotLayout } from "./plot";
import { CheckboxField } from "./ui";

const MetadataCard: Component<{
    record: SeismicRecord | undefined;
    loading: boolean;
    onNext: () => void;
    withMap: boolean;
    withWaveform: boolean;
    setWithMap: (value: boolean) => void;
    setWithWaveform: (value: boolean) => void;
}> = (props) => {
    const metadata = () => {
        const record = props.record;
        return [
            { label: "ID", value: record?.id ?? "---" },
            { label: "File Name", value: record?.file_name ?? "---" },
            { label: "Region", value: record?.region?.toUpperCase() ?? "---" },
            { label: "Category", value: record?.category?.toUpperCase() ?? "---" },
            { label: "Direction", value: record?.direction?.toUpperCase() ?? "---" },
            { label: "Magnitude", value: record?.magnitude ?? "---" },
            { label: "Depth (km)", value: record?.depth ?? "---" },
            {
                label: "PGA (Gal, cm/s^2)",
                value: record ? Math.abs(record.maximum_acceleration).toFixed(2) : "---",
            },
            {
                label: `Sampling Frequency (${record?.sampling_frequency_unit ?? "---"})`,
                value: record?.sampling_frequency ?? "---",
            },
            {
                label: "Event Time",
                value: record && record.event_time.getTime() !== 0 ? toUTC(record.event_time) : "---",
            },
            {
                label: "Record Time",
                value: record && record.record_time.getTime() !== 0 ? toUTC(record.record_time) : "---",
            },
            {
                label: "Last Update Time",
                value: record && record.last_update_time.getTime() !== 0 ? toUTC(record.last_update_time) : "---",
            },
        ];
    };

    return (
        <div class="panel jackpot-meta">
            <div class="meta-list">
                <For each={metadata()}>
                    {(item) => (
                        <>
                            <div class="meta-label">{item.label}</div>
                            <div class="meta-value">{item.value}</div>
                        </>
                    )}
                </For>
            </div>
            <div class="meta-actions">
                <CheckboxField
                    id="chk-map"
                    name="chk-map"
                    label="Map"
                    checked={props.withMap}
                    title="Show the event and station locations"
                    onCheckedChange={(checked) => (checked || props.withWaveform) && props.setWithMap(checked)}
                />
                <CheckboxField
                    id="chk-waveform"
                    name="chk-waveform"
                    label="Waveform"
                    checked={props.withWaveform}
                    title="Show the waveform"
                    onCheckedChange={(checked) => (checked || props.withMap) && props.setWithWaveform(checked)}
                />
                <button
                    id="btn-next"
                    class="icon-btn"
                    classList={{ loading: props.loading }}
                    onClick={props.onNext}
                    disabled={props.loading}
                    title="Get another random record from the database"
                    aria-label="Next record"
                    aria-busy={props.loading}
                >
                    <span class="spin-mark">↻</span>
                </button>
            </div>
        </div>
    );
};

const Epicenter: Component<{ record: SeismicRecord | undefined; class?: string }> = (props) => {
    const [map, setMap] = createSignal<L.Map>();
    let eventMarker: L.Marker | undefined;
    let stationMarker: L.Marker | undefined;

    onMount(() => {
        const current = DefaultMap("epicenter", new LatLng(52.5068441, 13.4247317));
        eventMarker = L.marker(current.getCenter(), { icon: epicenterIcon }).addTo(current);
        stationMarker = L.marker(current.getCenter(), { icon: stationIcon }).addTo(current);
        setMap(current);
    });

    createEffect(() => {
        const current = map();
        const record = props.record;
        if (!current || !record || !eventMarker || !stationMarker) return;

        const eventLocation = toLatLng(record.event_location);
        const stationLocation = toLatLng(record.station_location);

        current.flyTo(eventLocation, 6);
        eventMarker.setLatLng(eventLocation).bindPopup(`Event Location: ${eventLocation}`);
        stationMarker.setLatLng(stationLocation).bindPopup(`Station Location: ${stationLocation}`);
    });

    onCleanup(() => map()?.remove());

    return <div id="epicenter" class={`panel map ${props.class ?? ""}`} />;
};

const Waveform: Component<{ record: SeismicRecord | undefined; class?: string }> = (props) => {
    createEffect(async () => {
        const record = props.record;
        if (!record?.waveform?.length) return;

        await Plotly.newPlot(
            "canvas",
            [
                {
                    x: record.waveform.map((_, index) => index * record.time_interval),
                    y: record.waveform,
                    type: "scatter",
                    mode: "lines",
                    name: record.id,
                },
            ],
            plotLayout(record.file_name, {
                xaxis: plotAxis("Time (s)"),
                yaxis: plotAxis("Acceleration (cm/s^2)"),
            }),
            plotConfig,
        );
    });

    onCleanup(() => Plotly.purge("canvas"));

    return <div id="canvas" class={`panel map ${props.class ?? ""}`} />;
};

const Jackpot: Component = () => {
    const [record, { refetch }] = createResource(() => jackpot_waveform_api());
    const [withMap, setWithMap] = createSignal(true);
    const [withWaveform, setWithWaveform] = createSignal(true);

    return (
        <div class="jackpot-layout">
            <MetadataCard
                record={record()}
                loading={record.loading}
                onNext={() => refetch()}
                withMap={withMap()}
                withWaveform={withWaveform()}
                setWithMap={setWithMap}
                setWithWaveform={setWithWaveform}
            />
            {withMap() && <Epicenter record={record()} class="jackpot-plot" />}
            {withWaveform() && <Waveform record={record()} class="jackpot-wave" />}
        </div>
    );
};

export default Jackpot;
