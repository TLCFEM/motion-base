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
import { DefaultMap, epicenterIcon, selectedStationIcon, stationIcon } from "./Map";
import {
    Alert,
    AlertTitle,
    Box,
    Button,
    ButtonGroup,
    Card,
    CardContent,
    IconButton,
    LinearProgress,
    Modal,
    Paper,
    Stack,
    styled,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TextField,
} from "@suid/material";
import KeyboardArrowRightIcon from "@suid/icons-material/KeyboardArrowRight";
import KeyboardArrowLeftIcon from "@suid/icons-material/KeyboardArrowLeft";
import KeyboardDoubleArrowRightIcon from "@suid/icons-material/KeyboardDoubleArrowRight";
import KeyboardDoubleArrowLeftIcon from "@suid/icons-material/KeyboardDoubleArrowLeft";
import AddIcon from "@suid/icons-material/Add";
import RemoveIcon from "@suid/icons-material/Remove";
import { createDownloadLink, ifError, isNumeric, query_api, QueryConfig, SeismicRecord, sxProps, toUTC } from "./API";
import tippy from "tippy.js";
import "tippy.js/dist/tippy.css";
import "tippy.js/animations/scale.css";
import {
    ColumnDef,
    createSolidTable,
    flexRender,
    getCoreRowModel,
    getPaginationRowModel,
    getSortedRowModel,
    SortingState,
} from "@tanstack/solid-table";

const [pageSize, setPageSize] = createSignal(0);
const [pageNumber, setPageNumber] = createSignal(0);
const [minMagnitude, setMinMagnitude] = createSignal("");
const [maxMagnitude, setMaxMagnitude] = createSignal("");
const [minPGA, setMinPGA] = createSignal("");
const [maxPGA, setMaxPGA] = createSignal("");
const [fromDate, setFromDate] = createSignal<Date>(new Date(0));
const [toDate, setToDate] = createSignal<Date>(new Date(0));
const [fileName, setFileName] = createSignal("");
const [stationCode, setStationCode] = createSignal("");
const [eventLocation, setEventLocation] = createSignal<[number, number]>();
const [maxEventDistance, setMaxEventDistance] = createSignal(0);

const [records, setRecords] = createSignal([] as SeismicRecord[]);

const [error, setError] = createSignal("");

const Settings: Component<sxProps> = (props) => {
    const [loading, setLoading] = createSignal<boolean>(false);

    async function fetch() {
        setLoading(true);

        let config = new QueryConfig();
        if (pageSize() > 0) config.pagination.page_size = pageSize();
        if (pageNumber() > 0) config.pagination.page_number = pageNumber();
        // config.pagination.sort_by = "+event_time";
        if (isNumeric(minMagnitude()) && Number(minMagnitude()) > 0) config.min_magnitude = Number(minMagnitude());
        if (isNumeric(maxMagnitude()) && Number(maxMagnitude()) > 0) config.max_magnitude = Number(maxMagnitude());
        if (isNumeric(minPGA()) && Number(minPGA()) > 0) config.min_pga = Number(minPGA());
        if (isNumeric(maxPGA()) && Number(maxPGA()) > 0) config.max_pga = Number(maxPGA());
        if (fromDate().getTime() !== 0) config.from_date = fromDate();
        if (toDate().getTime() !== 0) config.to_date = toDate();
        if (eventLocation()) config.event_location = eventLocation();
        if (maxEventDistance() > 0) config.max_event_distance = maxEventDistance();
        if (fileName()) config.file_name = fileName();
        if (stationCode()) config.station_code = stationCode();

        try {
            setRecords(await query_api(config));
        } catch (e) {
            // clear();
            setError((e as Error).message);
        }

        setLoading(false);
    }

    function clear() {
        setPageSize(0);
        setPageNumber(0);
        setMinMagnitude("");
        setMaxMagnitude("");
        setMinPGA("");
        setMaxPGA("");
        setFromDate(new Date(0));
        setToDate(new Date(0));
        setFileName("");
        setStationCode("");

        setRecords([] as SeismicRecord[]);

        if (marker) {
            marker.remove();
            marker = undefined;
        }
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
        tippy(`#btn-save`, {
            content: "Save search results in json.",
            animation: "scale",
        });
        tippy(`#page-number`, {
            content: "The query results are paginated. Choose which page to be fetched.",
            animation: "scale",
        });
        tippy(`#page-size`, {
            content: "The query results are paginated. Assign the number of records per page.",
            animation: "scale",
        });
        tippy(`#min-magnitude`, {
            content: "The minimum magnitude of interest.",
            animation: "scale",
        });
        tippy(`#max-magnitude`, {
            content: "The maximum magnitude of interest.",
            animation: "scale",
        });
        tippy(`#min-pga`, {
            content: "The minimum PGA of interest.",
            animation: "scale",
        });
        tippy(`#max-pga`, {
            content: "The maximum PGA of interest.",
            animation: "scale",
        });
        tippy(`#from-date`, {
            content: "The date of the earthquake event.",
            animation: "scale",
        });
        tippy(`#to-date`, {
            content: "The date of the earthquake event.",
            animation: "scale",
        });
        tippy(`#file-name`, {
            content: "Regular expression to filter file names.",
            animation: "scale",
        });
        tippy(`#station-code`, {
            content: "Regular expression to filter station codes.",
            animation: "scale",
        });
    });

    const stackProps = {
        gap: "1rem",
        display: "flex",
        justifyContent: "center",
        alignContent: "center",
        alignItems: "stretch",
    };

    return (
        <Card sx={{ ...props.sx, display: "flex", flexDirection: "column" }}>
            <CardContent
                sx={{
                    display: "flex",
                    flexDirection: "row",
                    justifyContent: "center",
                    alignContent: "center",
                    alignItems: "center",
                    gap: "1rem",
                    flexGrow: 1,
                }}
            >
                <Stack sx={stackProps}>
                    <TextField
                        size="small"
                        id="page-number"
                        label="Page Number"
                        type="number"
                        value={pageNumber()}
                        onChange={(_, value) => setPageNumber(Math.max(Math.round(Number(value)), 0))}
                        disabled={loading()}
                    />
                    <TextField
                        size="small"
                        id="page-size"
                        label="Page Size"
                        type="number"
                        value={pageSize() > 0 ? pageSize() : ""}
                        onChange={(_, value) =>
                            setPageSize(value ? Math.max(Math.min(1000, Math.round(Number(value))), 1) : 0)
                        }
                        disabled={loading()}
                    />
                </Stack>
                <Stack sx={stackProps}>
                    <TextField
                        size="small"
                        id="min-magnitude"
                        error={ifError(minMagnitude())}
                        label="Min Magnitude"
                        type="number"
                        value={minMagnitude()}
                        onChange={(_, value) => setMinMagnitude(Number(value) > 10 ? "10" : value)}
                        disabled={loading()}
                    />
                    <TextField
                        size="small"
                        id="max-magnitude"
                        error={ifError(maxMagnitude())}
                        label="Max Magnitude"
                        type="number"
                        value={maxMagnitude()}
                        onChange={(_, value) => setMaxMagnitude(Number(value) > 10 ? "10" : value)}
                        disabled={loading()}
                    />
                </Stack>
                <Stack sx={stackProps}>
                    <TextField
                        size="small"
                        id="min-pga"
                        error={ifError(minPGA())}
                        label="Min PGA (Gal)"
                        type="number"
                        value={minPGA()}
                        onChange={(_, value) => setMinPGA(value)}
                        disabled={loading()}
                    />
                    <TextField
                        size="small"
                        id="max-pga"
                        error={ifError(maxPGA())}
                        label="Max PGA (Gal)"
                        type="number"
                        value={maxPGA()}
                        onChange={(_, value) => setMaxPGA(value)}
                        disabled={loading()}
                    />
                </Stack>
                <Stack sx={stackProps}>
                    <TextField
                        size="small"
                        sx={{ minWidth: "17ch" }}
                        id="from-date"
                        label="From"
                        type="date"
                        InputLabelProps={{ shrink: true }}
                        value={fromDate().getTime() === 0 ? "" : fromDate().toISOString().split("T")[0]}
                        onChange={(_, value) => setFromDate(value ? new Date(Date.parse(value)) : new Date(0))}
                        disabled={loading()}
                    />
                    <TextField
                        size="small"
                        sx={{ minWidth: "17ch" }}
                        id="to-date"
                        label="To"
                        type="date"
                        InputLabelProps={{ shrink: true }}
                        value={toDate().getTime() === 0 ? "" : toDate().toISOString().split("T")[0]}
                        onChange={(_, value) => setToDate(value ? new Date(Date.parse(value)) : new Date(0))}
                        disabled={loading()}
                    />
                </Stack>
                <Stack sx={stackProps}>
                    <TextField
                        size="small"
                        id="file-name"
                        label="File Name"
                        value={fileName()}
                        onChange={(_, value) => setFileName(value)}
                        disabled={loading()}
                    />
                    <TextField
                        size="small"
                        id="station-code"
                        label="Station Code"
                        value={stationCode()}
                        onChange={(_, value) => setStationCode(value)}
                        disabled={loading()}
                    />
                </Stack>
                <ButtonGroup variant="contained" orientation="vertical">
                    <Button size="small" onClick={fetch} id="btn-search" disabled={loading()}>
                        Search
                    </Button>
                    <Button size="small" onClick={clear} id="btn-clear" disabled={loading()}>
                        Clear
                    </Button>
                    <Button
                        size="small"
                        onClick={() => {
                            const element = createDownloadLink(records());
                            element.download = "search.json";
                            document.body.appendChild(element); // Required for this to work in FireFox
                            element.click();
                        }}
                        id="btn-save"
                        disabled={loading() || records().length === 0}
                    >
                        Download
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
            {loading() ? <LinearProgress /> : <LinearProgress variant="determinate" value={0} />}
        </Card>
    );
};

let marker: L.Marker;

const TanStackTable: Component<sxProps> = (props) => {
    const [tableSorting, setTableSorting] = createSignal<SortingState>([]);

    const [tablePageSize, setTablePageSize] = createSignal(10);
    const [tablePagination, setTablePagination] = createSignal({ pageIndex: 0, pageSize: tablePageSize() });

    createEffect(() => setTablePagination({ pageIndex: 0, pageSize: tablePageSize() }));

    const StyledTableRow = styled(TableRow)(({ theme }) => ({
        "&:nth-of-type(odd)": {
            backgroundColor: theme.palette.action.hover,
        },
        // "&:last-child td, &:last-child th": {
        //     border: 0,
        // },
    }));

    const columns: ColumnDef<SeismicRecord>[] = [
        {
            accessorKey: "id",
            header: "ID",
        },
        {
            accessorKey: "magnitude",
            header: "Magnitude",
        },
        {
            accessorKey: "maximum_acceleration",
            header: "PGA (Gal)",
            cell: (info) => Math.abs(info.getValue<number>()).toFixed(2),
        },
        {
            accessorKey: "depth",
            header: "Depth (km)",
        },
        {
            accessorKey: "duration",
            header: "Duration (s)",
            cell: (info) => Math.abs(info.getValue<number>()).toFixed(2),
        },
        {
            accessorKey: "event_time",
            header: "Event Time",
            cell: (info) => toUTC(info.getValue<Date>()),
        },
        {
            accessorKey: "station_code",
            header: "Station",
            cell: (info) => info.getValue<string>().toUpperCase(),
        },
        {
            accessorKey: "direction",
            header: "Component",
            cell: (info) => info.getValue<string>().toUpperCase(),
        },
    ];

    const table = createSolidTable({
        get data() {
            return records();
        },
        columns: columns,
        getCoreRowModel: getCoreRowModel(),
        onSortingChange: setTableSorting,
        getSortedRowModel: getSortedRowModel(),
        onPaginationChange: setTablePagination,
        getPaginationRowModel: getPaginationRowModel(),
        state: {
            get sorting() {
                return tableSorting();
            },
            get pagination() {
                return tablePagination();
            },
        },
    });

    onMount(() => {
        tippy(`#table-header`, {
            content: "Click header cells to sort results.",
            animation: "scale",
        });
    });

    return (
        <Card sx={{ ...props.sx, display: "flex", flexDirection: "column" }}>
            <TableContainer sx={{ overflow: "auto", flexGrow: 1 }}>
                <Table stickyHeader>
                    <TableHead id="table-header">
                        <For each={table.getHeaderGroups()}>
                            {(headerGroup) => (
                                <TableRow>
                                    <For each={headerGroup.headers}>
                                        {(header) => (
                                            <TableCell onClick={header.column.getToggleSortingHandler()}>
                                                {header.isPlaceholder
                                                    ? null
                                                    : flexRender(header.column.columnDef.header, header.getContext())}
                                            </TableCell>
                                        )}
                                    </For>
                                </TableRow>
                            )}
                        </For>
                    </TableHead>
                    <TableBody>
                        <For each={table.getRowModel().rows}>
                            {(row) => (
                                <StyledTableRow
                                    onClick={() => {
                                        if (marker) {
                                            if (marker.getPopup().getContent() === row.original.id) {
                                                marker.remove();
                                                marker = undefined;
                                                return;
                                            }

                                            marker.setLatLng(
                                                new LatLng(
                                                    row.original.station_location[1],
                                                    row.original.station_location[0],
                                                ),
                                            );
                                        } else {
                                            marker = L.marker(
                                                new LatLng(
                                                    row.original.station_location[1],
                                                    row.original.station_location[0],
                                                ),
                                                {
                                                    icon: selectedStationIcon,
                                                },
                                            ).addTo(map);
                                        }
                                        marker.bindPopup(row.original.id);
                                        marker.setZIndexOffset(1000);
                                        map.flyTo(marker.getLatLng(), map.getZoom());
                                    }}
                                >
                                    <For each={row.getVisibleCells()}>
                                        {(cell) => (
                                            <TableCell>
                                                {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                            </TableCell>
                                        )}
                                    </For>
                                </StyledTableRow>
                            )}
                        </For>
                    </TableBody>
                </Table>
            </TableContainer>
            <Box
                sx={{
                    display: "flex",
                    flexDirection: "row",
                    justifyContent: "center",
                    alignContent: "center",
                    alignItems: "center",
                    // gap: "1rem",
                }}
            >
                <IconButton
                    color="secondary"
                    onClick={() => setTablePageSize(tablePageSize() - 1)}
                    disabled={tablePageSize() <= 1}
                    sx={{ margin: "4px 2px 4px 4px" }}
                    size="small"
                >
                    <RemoveIcon />
                </IconButton>
                <IconButton
                    color="secondary"
                    onClick={() => setTablePageSize(tablePageSize() + 1)}
                    disabled={tablePageSize() >= records().length}
                    sx={{ margin: "4px 2px" }}
                    size="small"
                >
                    <AddIcon />
                </IconButton>
                <LinearProgress
                    color="secondary"
                    variant="determinate"
                    value={
                        table.getPageCount() === 0
                            ? 0
                            : (100 * (table.getState().pagination.pageIndex + 1)) / table.getPageCount()
                    }
                    sx={{ flexGrow: 1, margin: "4px 2px" }}
                />
                <IconButton
                    color="secondary"
                    onClick={() => table.firstPage()}
                    disabled={!table.getCanPreviousPage()}
                    sx={{ margin: "4px 2px" }}
                    size="small"
                >
                    <KeyboardDoubleArrowLeftIcon />
                </IconButton>
                <IconButton
                    color="secondary"
                    onClick={() => table.previousPage()}
                    disabled={!table.getCanPreviousPage()}
                    sx={{ margin: "4px 2px" }}
                    size="small"
                >
                    <KeyboardArrowLeftIcon />
                </IconButton>
                <IconButton
                    color="secondary"
                    onClick={() => table.nextPage()}
                    disabled={!table.getCanNextPage()}
                    sx={{ margin: "4px 2px" }}
                    size="small"
                >
                    <KeyboardArrowRightIcon />
                </IconButton>
                <IconButton
                    color="secondary"
                    onClick={() => table.lastPage()}
                    disabled={!table.getCanNextPage()}
                    sx={{ margin: "4px 4px 4px 2px" }}
                    size="small"
                >
                    <KeyboardDoubleArrowRightIcon />
                </IconButton>
            </Box>
        </Card>
    );
};

let map: L.Map;

const QueryDatabase: Component = () => {
    const normalize_longitude = (lon: number) => {
        while (lon < -180) lon += 360;
        while (lon > 180) lon -= 360;
        return lon;
    };

    const normalize_latitude = (lat: number) => {
        while (lat < -90) lat += 180;
        while (lat > 90) lat -= 180;
        return lat;
    };

    const update_location = () => {
        const bound = map.getBounds();

        setEventLocation([normalize_longitude(map.getCenter().lng), normalize_latitude(map.getCenter().lat)]);
        setMaxEventDistance(bound.getNorthEast().distanceTo(bound.getSouthWest()) / 2);
    };

    onMount(() => {
        map = DefaultMap("overview", new LatLng(-0.58725, 157.20725), 4);

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

                marker?.bindPopup(`Station Designation: ${record.station_code.toUpperCase()}`);
            } else {
                const marker = L.marker(new LatLng(record.station_location[1], record.station_location[0]), {
                    icon: stationIcon,
                }).addTo(map);

                marker.bindPopup(`Station Designation: ${record.station_code.toUpperCase()}`);
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
            <Paper id="overview" sx={{ border: "1px solid darkgrey", flexGrow: 1 }} />
            <Stack sx={{ display: "flex", width: "60%", height: "90vh" }} spacing="1rem">
                <Settings sx={{ border: "1px solid darkgrey", minHeight: "8rem" }} />
                <TanStackTable sx={{ border: "1px solid darkgrey", flexGrow: 1 }} />
            </Stack>
        </>
    );
};

export default QueryDatabase;
