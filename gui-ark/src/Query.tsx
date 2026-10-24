//  Copyright (C) 2022-2026 Theodore Chang
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.

import { Pagination } from "@ark-ui/solid/pagination";
import {
    createColumnHelper,
    createPaginatedRowModel,
    createSortedRowModel,
    createTable,
    FlexRender,
    PaginationState,
    rowPaginationFeature,
    rowSortingFeature,
    SortingState,
    tableFeatures,
} from "@tanstack/solid-table";
import L, { LatLng } from "leaflet";
import { Component, createEffect, createSignal, For, on, onCleanup, onMount } from "solid-js";
import { createStore, SetStoreFunction } from "solid-js/store";
import {
    buildQueryConfig,
    createDownloadLink,
    emptyQueryForm,
    errorMessage,
    ifError,
    query_api,
    QueryArea,
    QueryForm,
    SeismicRecord,
    toUTC,
} from "./api";
import { DefaultMap, epicenterIcon, selectedStationIcon, stationIcon } from "./Map";
import { ErrorDialog, TextField } from "./ui";

const features = tableFeatures({
    rowSortingFeature,
    rowPaginationFeature,
    sortedRowModel: createSortedRowModel(),
    paginatedRowModel: createPaginatedRowModel(),
});

const columnHelper = createColumnHelper<typeof features, SeismicRecord>();

const columns = columnHelper.columns([
    columnHelper.accessor("id", { header: "ID" }),
    columnHelper.accessor("magnitude", { header: "Magnitude" }),
    columnHelper.accessor("maximum_acceleration", {
        header: "PGA (Gal)",
        cell: (info) => Math.abs(info.getValue()).toFixed(2),
    }),
    columnHelper.accessor("depth", { header: "Depth (km)" }),
    columnHelper.accessor("duration", {
        header: "Duration (s)",
        cell: (info) => Math.abs(info.getValue()).toFixed(2),
    }),
    columnHelper.accessor("event_time", {
        header: "Event Time",
        cell: (info) => toUTC(info.getValue()),
    }),
    columnHelper.accessor("station_code", {
        header: "Station",
        cell: (info) => info.getValue().toUpperCase(),
    }),
    columnHelper.accessor("direction", {
        header: "Direction",
        cell: (info) => info.getValue().toUpperCase(),
    }),
]);

const clampInteger = (value: string, min: number, max: number) =>
    value === "" ? "" : String(Math.min(max, Math.max(min, Math.round(Number(value)))));

const Settings: Component<{
    form: QueryForm;
    setForm: SetStoreFunction<QueryForm>;
    loading: boolean;
    hasRecords: boolean;
    onSearch: () => void;
    onClear: () => void;
    onDownload: () => void;
}> = (props) => {
    return (
        <section class="panel query-settings">
            <div class="panel-body col">
                <div class="settings-grid">
                    <TextField
                        id="page-number"
                        label="Page Number"
                        type="number"
                        min={0}
                        value={props.form.pageNumber}
                        onValueChange={(value) => props.setForm("pageNumber", clampInteger(value, 0, 1_000_000))}
                        disabled={props.loading}
                        title="The query results are paginated. Choose which page to fetch."
                    />
                    <TextField
                        id="page-size"
                        label="Page Size"
                        type="number"
                        min={1}
                        max={1000}
                        value={props.form.pageSize}
                        onValueChange={(value) => props.setForm("pageSize", value === "" ? "" : clampInteger(value, 1, 1000))}
                        disabled={props.loading}
                        title="The number of records per page."
                    />
                    <TextField
                        id="min-magnitude"
                        label="Min Magnitude"
                        type="number"
                        min={0}
                        max={10}
                        step="any"
                        value={props.form.minMagnitude}
                        invalid={ifError(props.form.minMagnitude)}
                        onValueChange={(value) => props.setForm("minMagnitude", Number(value) > 10 ? "10" : value)}
                        disabled={props.loading}
                        title="The minimum magnitude of interest."
                    />
                    <TextField
                        id="max-magnitude"
                        label="Max Magnitude"
                        type="number"
                        min={0}
                        max={10}
                        step="any"
                        value={props.form.maxMagnitude}
                        invalid={ifError(props.form.maxMagnitude)}
                        onValueChange={(value) => props.setForm("maxMagnitude", Number(value) > 10 ? "10" : value)}
                        disabled={props.loading}
                        title="The maximum magnitude of interest."
                    />
                    <TextField
                        id="min-pga"
                        label="Min PGA (Gal)"
                        type="number"
                        min={0}
                        step="any"
                        value={props.form.minPGA}
                        invalid={ifError(props.form.minPGA)}
                        onValueChange={(value) => props.setForm("minPGA", value)}
                        disabled={props.loading}
                        title="The minimum PGA of interest."
                    />
                    <TextField
                        id="max-pga"
                        label="Max PGA (Gal)"
                        type="number"
                        min={0}
                        step="any"
                        value={props.form.maxPGA}
                        invalid={ifError(props.form.maxPGA)}
                        onValueChange={(value) => props.setForm("maxPGA", value)}
                        disabled={props.loading}
                        title="The maximum PGA of interest."
                    />
                    <TextField
                        id="from-date"
                        label="From"
                        type="date"
                        value={props.form.fromDate}
                        onValueChange={(value) => props.setForm("fromDate", value)}
                        disabled={props.loading}
                        title="The earliest event date."
                    />
                    <TextField
                        id="to-date"
                        label="To"
                        type="date"
                        value={props.form.toDate}
                        onValueChange={(value) => props.setForm("toDate", value)}
                        disabled={props.loading}
                        title="The latest event date."
                    />
                    <TextField
                        id="file-name"
                        label="File Name"
                        value={props.form.fileName}
                        onValueChange={(value) => props.setForm("fileName", value)}
                        disabled={props.loading}
                        title="Regular expression to filter file names."
                    />
                    <TextField
                        id="station-code"
                        label="Station Code"
                        value={props.form.stationCode}
                        onValueChange={(value) => props.setForm("stationCode", value)}
                        disabled={props.loading}
                        title="Regular expression to filter station codes."
                    />
                    <div class="settings-actions">
                        <button
                            class="btn"
                            classList={{ loading: props.loading }}
                            id="btn-search"
                            onClick={props.onSearch}
                            disabled={props.loading}
                            aria-busy={props.loading}
                        >
                            Search
                        </button>
                        <button class="btn secondary" id="btn-clear" onClick={props.onClear} disabled={props.loading}>
                            Clear
                        </button>
                        <button
                            class="btn secondary"
                            id="btn-save"
                            onClick={props.onDownload}
                            disabled={props.loading || !props.hasRecords}
                        >
                            Download
                        </button>
                    </div>
                </div>
            </div>
        </section>
    );
};

export const QueryTable: Component<{
    records: SeismicRecord[];
    selected?: SeismicRecord;
    onSelect: (record: SeismicRecord) => void;
}> = (props) => {
    const [sorting, setSorting] = createSignal<SortingState>([]);
    const [pagination, setPagination] = createSignal<PaginationState>({ pageIndex: 0, pageSize: 10 });

    const table = createTable({
        features,
        columns,
        get data() {
            return props.records;
        },
        state: {
            get sorting() {
                return sorting();
            },
            get pagination() {
                return pagination();
            },
        },
        onSortingChange: setSorting,
        onPaginationChange: setPagination,
    });

    createEffect(
        on(
            () => props.records,
            () => setPagination((current) => (current.pageIndex === 0 ? current : { ...current, pageIndex: 0 })),
            { defer: true },
        ),
    );

    const pageCount = () => Math.max(1, table.getPageCount());
    const page = () => Math.min(pagination().pageIndex + 1, pageCount());

    function changePageSize(delta: number) {
        setPagination((current) => ({
            ...current,
            pageIndex: 0,
            pageSize: Math.max(1, current.pageSize + delta),
        }));
    }

    return (
        <section class="panel query-table">
            <div class="table-wrap">
                <table class="data">
                    <thead id="table-header">
                        <For each={table.getHeaderGroups()}>
                            {(headerGroup) => (
                                <tr>
                                    <For each={headerGroup.headers}>
                                        {(header) => (
                                            <th onClick={header.column.getToggleSortingHandler()}>
                                                <FlexRender header={header} />
                                                <span class="sort-mark">
                                                    {header.column.getIsSorted() === "asc"
                                                        ? "▲"
                                                        : header.column.getIsSorted() === "desc"
                                                          ? "▼"
                                                          : ""}
                                                </span>
                                            </th>
                                        )}
                                    </For>
                                </tr>
                            )}
                        </For>
                    </thead>
                    <tbody>
                        <For each={table.getRowModel().rows}>
                            {(row) => (
                                <tr
                                    classList={{ selected: props.selected?.id === row.original.id }}
                                    onClick={() => props.onSelect(row.original)}
                                >
                                    <For each={row.getAllCells()}>
                                        {(cell) => (
                                            <td>
                                                <FlexRender cell={cell} />
                                            </td>
                                        )}
                                    </For>
                                </tr>
                            )}
                        </For>
                    </tbody>
                </table>
            </div>
            <div class="table-foot">
                <button
                    class="icon-btn"
                    onClick={() => changePageSize(-1)}
                    disabled={pagination().pageSize <= 1}
                    title="Fewer rows per page"
                    aria-label="Fewer rows per page"
                >
                    −
                </button>
                <button
                    class="icon-btn"
                    onClick={() => changePageSize(1)}
                    disabled={pagination().pageSize >= props.records.length}
                    title="More rows per page"
                    aria-label="More rows per page"
                >
                    +
                </button>
                <span class="muted">{pagination().pageSize} / page</span>
                <span class="muted" title="Records returned by the current search">
                    · {props.records.length} fetched
                </span>
                <span class="spacer" />
                {/* Ark's count is the number of items; pageSize makes its page count match the table's. */}
                <Pagination.Root
                    class="pager"
                    count={props.records.length}
                    pageSize={pagination().pageSize}
                    page={page()}
                    siblingCount={1}
                    onPageChange={(details) => table.setPageIndex(details.page - 1)}
                >
                    <Pagination.FirstTrigger class="page-btn" title="First page">
                        «
                    </Pagination.FirstTrigger>
                    <Pagination.PrevTrigger class="page-btn" title="Previous page">
                        ‹
                    </Pagination.PrevTrigger>
                    <span
                        class="page-count"
                        title={`Page ${page()} of ${pageCount()}`}
                        aria-label={`Page ${page()} of ${pageCount()}`}
                        aria-live="polite"
                    >
                        {page()} / {pageCount()}
                    </span>
                    <Pagination.NextTrigger class="page-btn" title="Next page">
                        ›
                    </Pagination.NextTrigger>
                    <Pagination.LastTrigger class="page-btn" title="Last page">
                        »
                    </Pagination.LastTrigger>
                </Pagination.Root>
            </div>
        </section>
    );
};

const QueryMap: Component<{
    records: SeismicRecord[];
    selected?: SeismicRecord;
    onAreaChange: (area: QueryArea) => void;
}> = (props) => {
    const [map, setMap] = createSignal<L.Map>();
    const stationMarkers = new Map<string, L.Marker>();
    const eventMarkers = new Map<string, L.Marker>();
    const eventIds = new Map<string, Set<string>>();
    let selectedMarker: L.Marker | undefined;

    const normalizeLongitude = (longitude: number) => {
        while (longitude < -180) longitude += 360;
        while (longitude > 180) longitude -= 360;
        return longitude;
    };

    const normalizeLatitude = (latitude: number) => {
        while (latitude < -90) latitude += 180;
        while (latitude > 90) latitude -= 180;
        return latitude;
    };

    function updateArea() {
        const current = map();
        if (!current) return;
        const bounds = current.getBounds();
        const center = current.getCenter();
        props.onAreaChange({
            location: [normalizeLongitude(center.lng), normalizeLatitude(center.lat)],
            distance: bounds.getNorthEast().distanceTo(bounds.getSouthWest()) / 2,
        });
    }

    onMount(() => {
        const current = DefaultMap("overview", new LatLng(-0.58725, 157.20725), 4);
        setMap(current);
        updateArea();
        current.on("moveend", updateArea);
    });

    createEffect(() => {
        const current = map();
        if (!current) return;

        for (const marker of stationMarkers.values()) marker.remove();
        for (const marker of eventMarkers.values()) marker.remove();
        stationMarkers.clear();
        eventMarkers.clear();
        eventIds.clear();

        for (const record of props.records) {
            const stationKey = record.station_location.join(",");
            const existingStation = stationMarkers.get(stationKey);
            if (existingStation) {
                existingStation.bindPopup(`Station Designation: ${record.station_code.toUpperCase()}`);
            } else {
                const marker = L.marker(new LatLng(record.station_location[1], record.station_location[0]), {
                    icon: stationIcon,
                }).addTo(current);
                marker.bindPopup(`Station Designation: ${record.station_code.toUpperCase()}`);
                stationMarkers.set(stationKey, marker);
            }

            const eventKey = record.event_location.join(",");
            let ids = eventIds.get(eventKey);
            if (!ids) {
                ids = new Set();
                eventIds.set(eventKey, ids);
            }
            ids.add(record.id);

            const existingEvent = eventMarkers.get(eventKey);
            if (existingEvent) {
                existingEvent.bindPopup([...ids].join("<br>"));
            } else {
                const marker = L.marker(new LatLng(record.event_location[1], record.event_location[0]), {
                    icon: epicenterIcon,
                }).addTo(current);
                marker.bindPopup([...ids].join("<br>"));
                eventMarkers.set(eventKey, marker);
            }
        }
    });

    createEffect(() => {
        const current = map();
        const record = props.selected;
        if (!current) return;

        selectedMarker?.remove();
        selectedMarker = undefined;

        if (!record) return;

        const location = new LatLng(record.station_location[1], record.station_location[0]);
        selectedMarker = L.marker(location, { icon: selectedStationIcon }).addTo(current);
        selectedMarker.bindPopup(record.id);
        selectedMarker.setZIndexOffset(9999);
        current.flyTo(location, current.getZoom());
    });

    onCleanup(() => map()?.remove());

    return <div id="overview" class="panel map query-map" />;
};

const QueryDatabase: Component = () => {
    const [form, setForm] = createStore<QueryForm>(emptyQueryForm());
    const [records, setRecords] = createSignal<SeismicRecord[]>([]);
    const [loading, setLoading] = createSignal(false);
    const [error, setError] = createSignal("");
    const [area, setArea] = createSignal<QueryArea>();
    const [selected, setSelected] = createSignal<SeismicRecord>();

    async function search() {
        setLoading(true);
        setError("");
        setSelected(undefined);
        try {
            setRecords(await query_api(buildQueryConfig(form, area())));
        } catch (err) {
            setError(errorMessage(err));
        } finally {
            setLoading(false);
        }
    }

    function clear() {
        setForm(emptyQueryForm());
        setRecords([]);
        setSelected(undefined);
        setError("");
    }

    function download() {
        const element = createDownloadLink(records());
        element.download = "search.json";
        document.body.appendChild(element);
        element.click();
        element.remove();
    }

    function select(record: SeismicRecord) {
        setSelected((current) => (current?.id === record.id ? undefined : record));
    }

    return (
        <div class="query-layout">
            <QueryMap records={records()} selected={selected()} onAreaChange={setArea} />
            <div class="query-side">
                <Settings
                    form={form}
                    setForm={setForm}
                    loading={loading()}
                    hasRecords={records().length > 0}
                    onSearch={search}
                    onClear={clear}
                    onDownload={download}
                />
                <QueryTable records={records()} selected={selected()} onSelect={select} />
            </div>
            <ErrorDialog open={error() !== ""} message={error()} onClose={() => setError("")} />
        </div>
    );
};

export default QueryDatabase;
