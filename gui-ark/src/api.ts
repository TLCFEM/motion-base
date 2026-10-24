//  Copyright (C) 2022-2026 Theodore Chang
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.

import axios from "axios";

export const DEFAULT_BASE_URL = "https://tlcfem.top/mb/api";

export const http = axios.create({
    baseURL: DEFAULT_BASE_URL,
    timeout: 30000,
});

export const getBaseUrl = () => http.defaults.baseURL ?? DEFAULT_BASE_URL;

export const setBaseUrl = (url: string) => {
    http.defaults.baseURL = url.trim().replace(/\/+$/, "");
};

export const errorMessage = (error: unknown) =>
    error instanceof Error ? error.message : typeof error === "string" ? error : "Unknown error";

export class SeismicRecord {
    public endpoint = "";
    public id = "---";
    public file_name = "---";
    public category = "---";
    public region = "---";
    public uploaded_by = "---";

    public magnitude = 0;
    public maximum_acceleration = 0;

    public event_time: Date = new Date(0);
    public event_location: number[] = [13.4247317, 52.5068441];
    public depth = 0;

    public station_code = "---";
    public station_location: number[] = [13.4247317, 52.5068441];
    public station_elevation = 0;
    public station_elevation_unit = "";
    public record_time: Date = new Date(0);
    public last_update_time: Date = new Date(0);

    public sampling_frequency = 0;
    public sampling_frequency_unit = "---";
    public duration = 0;
    public direction = "---";
    public scale_factor = 0;

    public time_interval = 0;
    public waveform: number[] = [];

    public frequency_interval = 0;
    public spectrum: number[] = [];

    public period: number[] = [];
    public displacement_spectrum: number[] = [];
    public velocity_spectrum: number[] = [];
    public acceleration_spectrum: number[] = [];

    constructor(data: any) {
        Object.assign(this, data);
        this.record_time = new Date(data?.record_time || 0);
        this.event_time = new Date(data?.event_time || 0);
        this.last_update_time = new Date(data?.last_update_time || 0);
        this.event_location = data?.event_location ?? [13.4247317, 52.5068441];
        this.station_location = data?.station_location ?? [13.4247317, 52.5068441];
    }
}

export interface PaginationConfig {
    page_size?: number;
    page_number?: number;
    sort_by?: string;
}

export interface QueryConfig {
    min_magnitude?: number;
    max_magnitude?: number;
    event_location?: number[];
    station_location?: number[];
    max_event_distance?: number;
    max_station_distance?: number;
    from_date?: Date;
    to_date?: Date;
    min_pga?: number;
    max_pga?: number;
    file_name?: string;
    station_code?: string;
    direction?: string;
    pagination: PaginationConfig;
}

interface QueryResponse {
    records: SeismicRecord[];
    pagination: { page_number: number; page_size: number; total: number };
}

interface TotalResponse {
    total: number[];
}

export interface AggregationItem {
    key: number;
    doc_count: number;
    key_as_string?: string;
}

interface StatsResponse {
    year: { buckets: AggregationItem[] };
    magnitude: { buckets: AggregationItem[] };
    pga: { buckets: AggregationItem[] };
}

export interface QueryForm {
    pageNumber: string;
    pageSize: string;
    minMagnitude: string;
    maxMagnitude: string;
    minPGA: string;
    maxPGA: string;
    fromDate: string;
    toDate: string;
    fileName: string;
    stationCode: string;
}

export interface QueryArea {
    location: [number, number];
    distance: number;
}

export const emptyQueryForm = (): QueryForm => ({
    pageNumber: "",
    pageSize: "",
    minMagnitude: "",
    maxMagnitude: "",
    minPGA: "",
    maxPGA: "",
    fromDate: "",
    toDate: "",
    fileName: "",
    stationCode: "",
});

export const isNumeric = (value: string) => /^[-+]?\d*\.?\d+$/.test(value);

export const ifError = (input: string) => input !== "" && (!isNumeric(input) || Number(input) <= 0);

const positive = (value: string) => (isNumeric(value) && Number(value) > 0 ? Number(value) : undefined);

export function buildQueryConfig(form: QueryForm, area?: QueryArea): QueryConfig {
    const config: QueryConfig = { pagination: {} };

    const pageSize = positive(form.pageSize);
    const pageNumber = positive(form.pageNumber);
    if (pageSize) config.pagination.page_size = Math.min(1000, Math.round(pageSize));
    if (pageNumber) config.pagination.page_number = Math.round(pageNumber);

    if (positive(form.minMagnitude)) config.min_magnitude = positive(form.minMagnitude);
    if (positive(form.maxMagnitude)) config.max_magnitude = positive(form.maxMagnitude);
    if (positive(form.minPGA)) config.min_pga = positive(form.minPGA);
    if (positive(form.maxPGA)) config.max_pga = positive(form.maxPGA);
    if (form.fromDate) config.from_date = new Date(form.fromDate);
    if (form.toDate) config.to_date = new Date(form.toDate);
    if (form.fileName) config.file_name = form.fileName;
    if (form.stationCode) config.station_code = form.stationCode;
    if (area) {
        config.event_location = area.location;
        config.max_event_distance = area.distance;
    }

    return config;
}

export interface ProcessConfig {
    up_ratio?: number;
    down_ratio?: number;
    filter_length?: number;
    filter_type?: string;
    window_type?: string;
    low_cut?: number;
    high_cut?: number;
    damping_ratio?: number;
    period_end?: number;
    period_step?: number;
    normalised?: boolean;
    with_filter?: boolean;
    with_spectrum?: boolean;
    with_response_spectrum?: boolean;
    remove_head?: number;
}

export interface ProcessForm {
    recordId: string;
    normalised: boolean;
    withFilter: boolean;
    withSpectrum: boolean;
    withResponseSpectrum: boolean;
    upRatio: string;
    downRatio: string;
    filterLength: string;
    filterType: string;
    windowType: string;
    lowCut: string;
    highCut: string;
    dampingRatio: string;
    periodStep: string;
    periodEnd: string;
    removeHead: string;
}

export const defaultProcessForm = (): ProcessForm => ({
    recordId: "",
    normalised: false,
    withFilter: false,
    withSpectrum: false,
    withResponseSpectrum: false,
    upRatio: "",
    downRatio: "",
    filterLength: "",
    filterType: "lowpass",
    windowType: "hann",
    lowCut: "",
    highCut: "",
    dampingRatio: "",
    periodStep: "",
    periodEnd: "",
    removeHead: "",
});

export function buildProcessConfig(form: ProcessForm): ProcessConfig {
    const config: ProcessConfig = {
        with_spectrum: form.withSpectrum,
        with_filter: form.withFilter,
        with_response_spectrum: form.withResponseSpectrum,
        filter_type: form.filterType,
        window_type: form.windowType,
    };

    if (form.normalised) config.normalised = true;
    if (positive(form.upRatio) > 1) config.up_ratio = Math.round(Number(form.upRatio));
    if (positive(form.downRatio) > 1) config.down_ratio = Math.round(Number(form.downRatio));
    if (positive(form.filterLength) > 8) config.filter_length = Math.round(Number(form.filterLength));
    if (positive(form.lowCut)) config.low_cut = Number(form.lowCut);
    if (positive(form.highCut)) config.high_cut = Number(form.highCut);
    if (positive(form.dampingRatio)) config.damping_ratio = Number(form.dampingRatio);
    if (positive(form.periodStep)) config.period_step = Number(form.periodStep);
    if (positive(form.periodEnd)) config.period_end = Number(form.periodEnd);
    if (positive(form.removeHead)) config.remove_head = Number(form.removeHead);

    return config;
}

export class ProcessResponse extends SeismicRecord {
    process_config?: ProcessConfig;
}

export async function jackpot_waveform_api() {
    return new SeismicRecord((await http.get("/waveform/jackpot")).data);
}

export async function query_api(config: QueryConfig) {
    const response = (await http.post<QueryResponse>("/search", config)).data;
    return response.records.map((record) => new SeismicRecord(record));
}

export async function get_total_api() {
    return (await http.get<TotalResponse>("/total")).data.total[0];
}

export async function get_stats() {
    return (await http.get<StatsResponse>("/stats")).data;
}

export async function post_total_api(configs: QueryConfig[]) {
    return (await http.post<TotalResponse>("/total", configs)).data.total;
}

export async function process_api(record_id: string, config: ProcessConfig) {
    const data = (await http.post<ProcessResponse>(`/process?record_id=${encodeURIComponent(record_id)}`, config)).data;
    return Object.assign(new SeismicRecord(data), data) as ProcessResponse;
}

export const toUTC = (date: Date) => new Date(date.getTime() - date.getTimezoneOffset() * 60000).toUTCString();

export function createDownloadLink(obj: unknown) {
    const element = document.createElement("a");
    const file = new Blob(
        [JSON.stringify(obj, (_, value) => (value === null || value === undefined || value?.length === 0 ? undefined : value))],
        { type: "application/json" },
    );
    element.href = URL.createObjectURL(file);
    return element;
}

export async function check_backend(retry = 3, backoff = 3000) {
    for (let attempt = 0; attempt <= retry; attempt++) {
        try {
            await http.get("/alive", { timeout: 3000 });
            return true;
        } catch {
            if (attempt === retry) return false;
            await new Promise((resolve) => setTimeout(resolve, backoff));
        }
    }

    return false;
}
