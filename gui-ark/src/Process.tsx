//  Copyright (C) 2022-2026 Theodore Chang
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.

import { Component, createEffect, createSignal, For, onCleanup, Show } from "solid-js";
import { createStore, SetStoreFunction } from "solid-js/store";
import Plotly from "plotly.js-basic-dist-min";
import {
    buildProcessConfig,
    createDownloadLink,
    defaultProcessForm,
    errorMessage,
    ifError,
    process_api,
    ProcessForm,
    ProcessResponse,
} from "./api";
import { plotAxis, plotConfig, plotLayout } from "./plot";
import { CheckboxField, ErrorDialog, SelectField, TextField } from "./ui";

const filterOptions = [
    { label: "Lowpass", value: "lowpass" },
    { label: "Highpass", value: "highpass" },
    { label: "Bandpass", value: "bandpass" },
];

const windowOptions = [
    { label: "FlatTop", value: "flattop" },
    { label: "BlackmanHarris", value: "blackmanharris" },
    { label: "Nuttall", value: "nuttall" },
    { label: "Hann", value: "hann" },
    { label: "Hamming", value: "hamming" },
    { label: "Kaiser", value: "kaiser" },
    { label: "ChebWin", value: "chebwin" },
];

const Settings: Component<{
    form: ProcessForm;
    setForm: SetStoreFunction<ProcessForm>;
    loading: boolean;
    hasResult: boolean;
    withWaveform: boolean;
    withEnergy: boolean;
    withLogScale: boolean;
    setWithWaveform: (value: boolean) => void;
    setWithEnergy: (value: boolean) => void;
    setWithLogScale: (value: boolean) => void;
    onProcess: () => void;
    onReset: () => void;
    onDownload: () => void;
}> = (props) => {
    const filterDisabled = () => !props.form.withFilter;
    const responseDisabled = () => !props.form.withResponseSpectrum;

    return (
        <section class="panel process-settings">
            <div class="process-row">
                <CheckboxField
                    id="chk-waveform"
                    label="Waveform"
                    checked={props.withWaveform}
                    onCheckedChange={props.setWithWaveform}
                    title="Display the original waveform."
                />
                <CheckboxField
                    id="chk-normalised"
                    label="Normalised"
                    checked={props.form.normalised}
                    onCheckedChange={(checked) => props.setForm("normalised", checked)}
                    title="Normalise the PGA to unity."
                />
                <CheckboxField
                    id="chk-frequency-spectrum"
                    label="Frequency Spectrum"
                    checked={props.form.withSpectrum}
                    onCheckedChange={(checked) => props.setForm("withSpectrum", checked)}
                    title="Compute the frequency spectrum of the original waveform."
                />
                <CheckboxField
                    id="chk-logscale"
                    label="Logscale"
                    checked={props.withLogScale}
                    onCheckedChange={props.setWithLogScale}
                    title="Use a logarithmic frequency axis."
                />
                <CheckboxField
                    id="chk-energy"
                    label="Energy Accumulation"
                    checked={props.withEnergy}
                    onCheckedChange={props.setWithEnergy}
                    title="Compute the energy accumulation based on the frequency spectrum."
                />
                <TextField
                    class="wide"
                    id="record-id"
                    label="ID"
                    value={props.form.recordId}
                    onValueChange={(value) => props.setForm("recordId", value)}
                    title="The record identifier to process."
                />
                <TextField
                    id="remove-head"
                    label="Remove Head (s)"
                    type="number"
                    min={0}
                    step="any"
                    value={props.form.removeHead}
                    invalid={ifError(props.form.removeHead)}
                    onValueChange={(value) => props.setForm("removeHead", value)}
                    title="Remove the first few seconds, default is zero."
                />
            </div>

            <div class="process-row">
                <CheckboxField
                    id="chk-filter"
                    label="Apply Filter"
                    checked={props.form.withFilter}
                    onCheckedChange={(checked) => props.setForm("withFilter", checked)}
                    title="Further process the record by applying a filter."
                />
                <TextField
                    id="upsampling-ratio"
                    label="Upsampling"
                    type="number"
                    min={1}
                    value={props.form.upRatio}
                    onValueChange={(value) => props.setForm("upRatio", value)}
                    disabled={filterDisabled()}
                    title="Assign a positive integer to upsample the record, default is one."
                />
                <TextField
                    id="downsampling-ratio"
                    label="Downsampling"
                    type="number"
                    min={1}
                    value={props.form.downRatio}
                    onValueChange={(value) => props.setForm("downRatio", value)}
                    disabled={filterDisabled()}
                    title="Assign a positive integer to downsample the record, default is one."
                />
                <TextField
                    id="filter-length"
                    label="Filter Length"
                    type="number"
                    min={8}
                    value={props.form.filterLength}
                    invalid={props.form.filterLength !== "" && Number(props.form.filterLength) < 8}
                    onValueChange={(value) => props.setForm("filterLength", value)}
                    disabled={filterDisabled()}
                    title="Assign a positive integer (at least eight) to set the filter window length, default is 32."
                />
                <TextField
                    id="low-cut"
                    label="Low Cut (Hz)"
                    type="number"
                    min={0}
                    step="any"
                    value={props.form.lowCut}
                    invalid={ifError(props.form.lowCut)}
                    onValueChange={(value) => props.setForm("lowCut", value)}
                    disabled={filterDisabled() || props.form.filterType === "lowpass"}
                    title="The low-cut frequency for highpass and bandpass filters, default is 0.01."
                />
                <TextField
                    id="high-cut"
                    label="High Cut (Hz)"
                    type="number"
                    min={0}
                    step="any"
                    value={props.form.highCut}
                    invalid={ifError(props.form.highCut)}
                    onValueChange={(value) => props.setForm("highCut", value)}
                    disabled={filterDisabled() || props.form.filterType === "highpass"}
                    title="The high-cut frequency for lowpass and bandpass filters, default is 50."
                />
                <SelectField
                    id="select-filter"
                    label="Filter Type"
                    value={props.form.filterType}
                    options={filterOptions}
                    onValueChange={(value) => props.setForm("filterType", value)}
                    disabled={filterDisabled()}
                />
                <SelectField
                    id="select-window"
                    label="Window Type"
                    value={props.form.windowType}
                    options={windowOptions}
                    onValueChange={(value) => props.setForm("windowType", value)}
                    disabled={filterDisabled()}
                />
            </div>

            <div class="process-row">
                <CheckboxField
                    id="chk-response-spectrum"
                    label="Compute Response Spectrum"
                    checked={props.form.withResponseSpectrum}
                    onCheckedChange={(checked) => props.setForm("withResponseSpectrum", checked)}
                    title="Compute response spectra of the original waveform."
                />
                <TextField
                    id="damping-ratio"
                    label="Damping Ratio"
                    type="number"
                    min={0}
                    step="any"
                    value={props.form.dampingRatio}
                    invalid={ifError(props.form.dampingRatio)}
                    onValueChange={(value) => props.setForm("dampingRatio", value)}
                    disabled={responseDisabled()}
                    title="Assign a positive damping ratio, default is 0.05."
                />
                <TextField
                    id="period-step"
                    label="Period Step (s)"
                    type="number"
                    min={0}
                    step="any"
                    value={props.form.periodStep}
                    invalid={ifError(props.form.periodStep)}
                    onValueChange={(value) => props.setForm("periodStep", value)}
                    disabled={responseDisabled()}
                    title="The period interval for the response spectrum, default is 0.01."
                />
                <TextField
                    id="period-end"
                    label="Period End (s)"
                    type="number"
                    min={0}
                    step="any"
                    value={props.form.periodEnd}
                    invalid={ifError(props.form.periodEnd)}
                    onValueChange={(value) => props.setForm("periodEnd", value)}
                    disabled={responseDisabled()}
                    title="The termination period for the response spectrum, default is 10."
                />
                <div class="process-buttons">
                    <button
                        class="btn"
                        classList={{ loading: props.loading }}
                        id="btn-process"
                        onClick={props.onProcess}
                        disabled={props.loading || !props.form.recordId.trim()}
                        aria-busy={props.loading}
                    >
                        Process
                    </button>
                    <button class="btn secondary" id="btn-reset" onClick={props.onReset} disabled={props.loading}>
                        Reset
                    </button>
                    <button class="btn secondary" id="btn-download" onClick={props.onDownload} disabled={props.loading || !props.hasResult}>
                        Download
                    </button>
                </div>
            </div>
        </section>
    );
};

const lineTrace = (record: ProcessResponse, x: number[], y: number[]): Partial<Plotly.PlotData> => ({
    x,
    y,
    type: "scatter",
    mode: "lines",
    name: record.id,
});

const historyTrace = (record: ProcessResponse, x: number[], y: number[]): Plotly.Data => ({
    ...lineTrace(record, x, y),
    line: { color: "rgba(13, 148, 136, 0.22)", width: 1 },
});

const Waveform: Component<{ current: ProcessResponse; history: ProcessResponse[] }> = (props) => {
    createEffect(async () => {
        const traces: Plotly.Data[] = [];

        for (const record of props.history) {
            if (!record.waveform?.length) continue;
            traces.push(
                historyTrace(
                    record,
                    record.waveform.map((_, index) => index * record.time_interval),
                    record.waveform,
                ),
            );
        }

        traces.push(
            lineTrace(
                props.current,
                props.current.waveform.map((_, index) => index * props.current.time_interval),
                props.current.waveform,
            ),
        );

        await Plotly.newPlot(
            "time",
            traces,
            plotLayout(props.current.file_name, {
                xaxis: plotAxis("Time (s)"),
                yaxis: plotAxis("Acceleration (cm/s^2)"),
                showlegend: false,
            }),
            plotConfig,
        );
    });

    onCleanup(() => Plotly.purge("time"));

    return <div id="time" class="panel plot" />;
};

const FrequencySpectrum: Component<{ current: ProcessResponse; history: ProcessResponse[]; logScale: boolean }> = (props) => {
    createEffect(async () => {
        const traces: Plotly.Data[] = [];

        for (const record of props.history) {
            if (!record.spectrum?.length) continue;
            traces.push(
                historyTrace(
                    record,
                    record.spectrum.map((_, index) => index * record.frequency_interval),
                    record.spectrum,
                ),
            );
        }

        traces.push(
            lineTrace(
                props.current,
                props.current.spectrum.map((_, index) => index * props.current.frequency_interval),
                props.current.spectrum,
            ),
        );

        await Plotly.newPlot(
            "spectrum",
            traces,
            plotLayout(props.current.file_name, {
                xaxis: plotAxis("Frequency (Hz)"),
                yaxis: plotAxis("Acceleration (cm/s^2)", { type: props.logScale ? "log" : "linear" }),
                showlegend: false,
            }),
            plotConfig,
        );
    });

    onCleanup(() => Plotly.purge("spectrum"));

    return <div id="spectrum" class="panel plot" />;
};

const accumulatedEnergy = (spectrum: number[]) => {
    const accumulated: number[] = [];
    for (const value of spectrum) accumulated.push((accumulated.at(-1) ?? 0) + value * value);
    const total = accumulated.at(-1) ?? 1;
    return accumulated.map((value) => (value / total) * 100);
};

const EnergyAccumulation: Component<{ current: ProcessResponse; history: ProcessResponse[] }> = (props) => {
    createEffect(async () => {
        const traces: Plotly.Data[] = [];

        for (const record of props.history) {
            if (!record.spectrum?.length) continue;
            traces.push(
                historyTrace(
                    record,
                    record.spectrum.map((_, index) => index * record.frequency_interval),
                    accumulatedEnergy(record.spectrum),
                ),
            );
        }

        traces.push(
            lineTrace(
                props.current,
                props.current.spectrum.map((_, index) => index * props.current.frequency_interval),
                accumulatedEnergy(props.current.spectrum),
            ),
        );

        await Plotly.newPlot(
            "energy",
            traces,
            plotLayout(props.current.file_name, {
                xaxis: plotAxis("Frequency (Hz)"),
                yaxis: plotAxis("Accumulated Energy (%)"),
                showlegend: false,
            }),
            plotConfig,
        );
    });

    onCleanup(() => Plotly.purge("energy"));

    return <div id="energy" class="panel plot" />;
};

const ResponseSpectrum: Component<{ current: ProcessResponse; history: ProcessResponse[] }> = (props) => {
    createEffect(async () => {
        const acceleration: Plotly.Data[] = [];
        const velocity: Plotly.Data[] = [];
        const displacement: Plotly.Data[] = [];

        for (const record of props.history) {
            if (record.acceleration_spectrum?.length) acceleration.push(historyTrace(record, record.period, record.acceleration_spectrum));
            if (record.velocity_spectrum?.length) velocity.push(historyTrace(record, record.period, record.velocity_spectrum));
            if (record.displacement_spectrum?.length) displacement.push(historyTrace(record, record.period, record.displacement_spectrum));
        }

        acceleration.push(lineTrace(props.current, props.current.period, props.current.acceleration_spectrum));
        velocity.push(lineTrace(props.current, props.current.period, props.current.velocity_spectrum));
        displacement.push(lineTrace(props.current, props.current.period, props.current.displacement_spectrum));

        const spectrumLayout = (title: string) =>
            plotLayout(props.current.file_name, {
                xaxis: plotAxis("Period (s)"),
                yaxis: plotAxis(title),
                showlegend: false,
            });

        await Plotly.newPlot("a_spectrum", acceleration, spectrumLayout("Acceleration (cm/s^2)"), plotConfig);
        await Plotly.newPlot("v_spectrum", velocity, spectrumLayout("Velocity (cm/s)"), plotConfig);
        await Plotly.newPlot("u_spectrum", displacement, spectrumLayout("Displacement (cm)"), plotConfig);
    });

    onCleanup(() => {
        Plotly.purge("a_spectrum");
        Plotly.purge("v_spectrum");
        Plotly.purge("u_spectrum");
    });

    return <For each={["a_spectrum", "v_spectrum", "u_spectrum"]}>{(id) => <div id={id} class="panel plot" />}</For>;
};

const Process: Component = () => {
    const [form, setForm] = createStore<ProcessForm>(defaultProcessForm());
    const [results, setResults] = createSignal<ProcessResponse[]>([]);
    const [loading, setLoading] = createSignal(false);
    const [error, setError] = createSignal("");
    const [withWaveform, setWithWaveform] = createSignal(true);
    const [withEnergy, setWithEnergy] = createSignal(false);
    const [withLogScale, setWithLogScale] = createSignal(false);

    const current = () => results().at(-1);
    const history = () => results().slice(0, -1);

    async function process() {
        const id = form.recordId.trim();
        if (!id) return;

        setLoading(true);
        setError("");
        try {
            const result = await process_api(id, buildProcessConfig(form));
            setResults((currentResults) => [...currentResults, result]);
        } catch (err) {
            setError(errorMessage(err));
        } finally {
            setLoading(false);
        }
    }

    function reset() {
        setForm(defaultProcessForm());
        setResults([]);
        setError("");
    }

    function download() {
        const record = current();
        if (!record) return;
        const element = createDownloadLink(record);
        element.download = `${record.id}.json`;
        document.body.appendChild(element);
        element.click();
        element.remove();
    }

    return (
        <div class="process-layout">
            <Settings
                form={form}
                setForm={setForm}
                loading={loading()}
                hasResult={!!current()}
                withWaveform={withWaveform()}
                withEnergy={withEnergy()}
                withLogScale={withLogScale()}
                setWithWaveform={setWithWaveform}
                setWithEnergy={setWithEnergy}
                setWithLogScale={setWithLogScale}
                onProcess={process}
                onReset={reset}
                onDownload={download}
            />

            <Show when={withWaveform() && current()?.waveform?.length}>
                <Waveform current={current()!} history={history()} />
            </Show>
            <Show when={form.withSpectrum && current()?.spectrum?.length}>
                <FrequencySpectrum current={current()!} history={history()} logScale={withLogScale()} />
            </Show>
            <Show when={form.withSpectrum && withEnergy() && current()?.spectrum?.length}>
                <EnergyAccumulation current={current()!} history={history()} />
            </Show>
            <Show when={form.withResponseSpectrum && current()?.period?.length}>
                <ResponseSpectrum current={current()!} history={history()} />
            </Show>

            <ErrorDialog open={error() !== ""} message={error()} onClose={() => setError("")} />
        </div>
    );
};

export default Process;
