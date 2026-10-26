import { describe, expect, it } from "vitest";
import {
    buildProcessConfig,
    buildQueryConfig,
    defaultProcessForm,
    emptyQueryForm,
    isNumeric,
    ifError,
    SeismicRecord,
    toUTC,
} from "../src/api";

describe("SeismicRecord", () => {
    it("fills safe defaults for missing metadata", () => {
        const record = new SeismicRecord({});

        expect(record.id).toBe("---");
        expect(record.event_time.getTime()).toBe(0);
        expect(record.event_location).toEqual([13.4247317, 52.5068441]);
        expect(record.waveform).toEqual([]);
    });

    it("parses dates and keeps server coordinates", () => {
        const record = new SeismicRecord({
            id: "abc",
            event_time: "2016-11-13T11:02:56",
            event_location: [173.02, -42.69],
            station_location: [173.054, -42.619],
        });

        expect(record.id).toBe("abc");
        expect(record.event_time).toBeInstanceOf(Date);
        expect(record.event_location).toEqual([173.02, -42.69]);
        expect(record.station_location).toEqual([173.054, -42.619]);
    });
});

describe("query helpers", () => {
    it("recognises valid positive numbers", () => {
        expect(isNumeric("12.5")).toBe(true);
        expect(isNumeric("abc")).toBe(false);
        expect(ifError("")).toBe(false);
        expect(ifError("0")).toBe(true);
        expect(ifError("-2")).toBe(true);
    });

    it("omits empty fields", () => {
        expect(buildQueryConfig(emptyQueryForm())).toEqual({ pagination: {} });
    });

    it("maps form values to the backend query shape", () => {
        const config = buildQueryConfig(
            {
                ...emptyQueryForm(),
                pageNumber: "2",
                pageSize: "25",
                minMagnitude: "5.5",
                maxMagnitude: "8",
                minPGA: "100",
                maxPGA: "900",
                fromDate: "2011-01-01",
                toDate: "2012-01-01",
                fileName: "*.V2A",
                stationCode: "ABC",
            },
            { location: [140, 35], distance: 250 },
        );

        expect(config.pagination).toEqual({ page_size: 25, page_number: 2 });
        expect(config.min_magnitude).toBe(5.5);
        expect(config.max_magnitude).toBe(8);
        expect(config.min_pga).toBe(100);
        expect(config.max_pga).toBe(900);
        expect(config.from_date).toEqual(new Date("2011-01-01"));
        expect(config.to_date).toEqual(new Date("2012-01-01"));
        expect(config.file_name).toBe("*.V2A");
        expect(config.station_code).toBe("ABC");
        expect(config.event_location).toEqual([140, 35]);
        expect(config.max_event_distance).toBe(250);
    });

    it("clamps the page size to the server limit", () => {
        const config = buildQueryConfig({ ...emptyQueryForm(), pageSize: "5000" });
        expect(config.pagination.page_size).toBe(1000);
    });
});

describe("process helpers", () => {
    it("always sends the boolean processing flags", () => {
        const config = buildProcessConfig(defaultProcessForm());

        expect(config.with_filter).toBe(false);
        expect(config.with_spectrum).toBe(false);
        expect(config.with_response_spectrum).toBe(false);
        expect(config.filter_type).toBe("lowpass");
        expect(config.window_type).toBe("hann");
        expect(config.normalised).toBeUndefined();
        expect(config.up_ratio).toBeUndefined();
    });

    it("maps valid numeric options and drops defaults", () => {
        const config = buildProcessConfig({
            ...defaultProcessForm(),
            normalised: true,
            withFilter: true,
            withSpectrum: true,
            withResponseSpectrum: true,
            upRatio: "2",
            downRatio: "1",
            filterLength: "8",
            filterType: "bandpass",
            windowType: "kaiser",
            lowCut: "0.1",
            highCut: "40",
            dampingRatio: "0.05",
            periodStep: "0.02",
            periodEnd: "8",
            removeHead: "1.5",
        });

        expect(config.normalised).toBe(true);
        expect(config.with_filter).toBe(true);
        expect(config.with_spectrum).toBe(true);
        expect(config.with_response_spectrum).toBe(true);
        expect(config.up_ratio).toBe(2);
        expect(config.down_ratio).toBeUndefined();
        expect(config.filter_length).toBeUndefined();
        expect(config.filter_type).toBe("bandpass");
        expect(config.window_type).toBe("kaiser");
        expect(config.low_cut).toBe(0.1);
        expect(config.high_cut).toBe(40);
        expect(config.damping_ratio).toBe(0.05);
        expect(config.period_step).toBe(0.02);
        expect(config.period_end).toBe(8);
        expect(config.remove_head).toBe(1.5);
    });
});

describe("toUTC", () => {
    it("renders the wall-clock time as UTC", () => {
        const date = new Date(2016, 10, 13, 11, 2, 56);
        expect(toUTC(date)).toContain("13 Nov 2016 11:02:56 GMT");
    });
});
