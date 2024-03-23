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

import axios from "axios";

axios.defaults.baseURL = "http://127.0.0.1:8000";

export class SeismicRecord {
    public endpoint: string = "";

    public id: string = "";
    public file_name: string = "";
    public category: string = "";
    public region: string = "";
    public uploaded_by: string = "";

    public magnitude: number = 0;
    public maximum_acceleration: number = 0;

    public event_time: Date = new Date(0);
    public event_location: Array<number> = Array<number>(2);
    public depth: number = 0;

    public station_code: string = "";
    public station_location: Array<number> = Array<number>(2);
    public station_elevation: number = 0;
    public station_elevation_unit: string = "";
    public record_time: Date = new Date(0);

    public sampling_frequency: number = 0;
    public sampling_frequency_unit: string = "";
    public duration: number = 0;
    public direction: string = "";
    public scale_factor: number = 0;

    public time_interval: number = 0;
    public waveform: Array<number> = Array<number>(0);

    public frequency_interval: number = 0;
    public spectrum: Array<number> = Array<number>(0);

    public period: Array<number> = Array<number>(0);
    public displacement_spectrum: Array<number> = Array<number>(0);
    public velocity_spectrum: Array<number> = Array<number>(0);
    public acceleration_spectrum: Array<number> = Array<number>(0);

    public constructor(data: any) {
        Object.assign(this, data);
        this.record_time = new Date(data?.record_time ? data?.record_time : 0);
        this.event_time = new Date(data?.event_time ? data?.event_time : 0);
        if (data?.event_location) {
            this.event_location = data?.event_location;
        } else {
            this.event_location = [13.4247317, 52.5068441];
        }
        if (data?.station_location) {
            this.station_location = data?.station_location;
        } else {
            this.station_location = [13.4247317, 52.5068441];
        }
    }
}

export async function jackpot_waveform_api() {
    return new SeismicRecord((await axios.get("/waveform/jackpot")).data);
}

export class QueryConfig {
    public min_magnitude: number | undefined;
    public max_magnitude: number | undefined;
    public event_location: number[] | undefined;

    public station_location: number[] | undefined;

    public max_event_distance: number | undefined;
    public max_station_distance: number | undefined;
    public from_date: Date | undefined;
    public to_date: Date | undefined;
    public min_pga: number | undefined;
    public max_pga: number | undefined;
    public event_name: string | undefined;
    public direction: string | undefined;
    public page_size: number | undefined;
    public page_number: number | undefined;
}

interface QueryResponse {
    records: SeismicRecord[];
}

export async function query_api(config: QueryConfig) {
    return (
        await axios.post<QueryResponse>(
            "/query",
            JSON.stringify(config, (_, value) =>
                value === null || value === undefined ? undefined : value,
            ),
            {
                headers: { "Content-Type": "application/json" },
            },
        )
    ).data.records.map((record) => new SeismicRecord(record));
}

interface TotalResponse {
    total: number;
}

export async function total_api() {
    return (await axios.get<TotalResponse>("/total")).data.total;
}
