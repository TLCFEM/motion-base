import { Component, createEffect, createSignal, For, onMount } from "solid-js";
import tippy from "tippy.js";
import {
    Alert,
    AlertTitle,
    Box,
    Button,
    ButtonGroup,
    Card,
    CardContent,
    Checkbox,
    FormControl,
    FormControlLabel,
    Grid,
    InputLabel,
    LinearProgress,
    MenuItem,
    Modal,
    Paper,
    Select,
    TextField,
} from "@suid/material";
import { ifError, isNumeric, process_api, ProcessConfig, ProcessResponse } from "./API";
import Plotly from "plotly.js-dist-min";

const [processed, setProcessed] = createSignal<ProcessResponse>({} as ProcessResponse);
const [error, setError] = createSignal("");
const [loading, setLoading] = createSignal(false);

const [withFilter, setWithFilter] = createSignal(false);
const [withSpectrum, setWithSpectrum] = createSignal(false);
const [withResponseSpectrum, setWithResponseSpectrum] = createSignal(false);

const [lowCut, setLowCut] = createSignal("");
const [highCut, setHighCut] = createSignal("");
const [ratio, setRatio] = createSignal(0);
const [filterLength, setFilterLength] = createSignal(0);
const [filterType, setFilterType] = createSignal("lowpass");
const [windowType, setWindowType] = createSignal("hann");

const [dampingRatio, setDampingRatio] = createSignal("");
const [periodStep, setPeriodStep] = createSignal("");
const [periodEnd, setPeriodEnd] = createSignal("");

const resizePlot = () => {
    Plotly.relayout("time", {}).then();
    Plotly.relayout("spectrum", {}).then();
    Plotly.relayout("a_spectrum", {}).then();
    Plotly.relayout("v_spectrum", {}).then();
    Plotly.relayout("u_spectrum", {}).then();
};

const Settings: Component = () => {
    const [currentRecord, setCurrentRecord] = createSignal("14064834-afa0-4f52-a5b6-bce03ea6f415");

    function clear() {
        setWithFilter(false);
        setWithSpectrum(false);
        setWithResponseSpectrum(false);

        setLowCut("");
        setHighCut("");
        setRatio(0);
        setFilterLength(0);
        setFilterType("lowpass");
        setWindowType("hann");

        setDampingRatio("");
        setPeriodStep("");
        setPeriodEnd("");

        setProcessed({} as ProcessResponse);
    }

    async function process() {
        setLoading(true);

        let config = new ProcessConfig();

        config.with_spectrum = withSpectrum();

        config.with_filter = withFilter();
        if (ratio() > 0) config.ratio = ratio();
        if (isNumeric(lowCut()) && Number(lowCut()) > 0) config.low_cut = Number(lowCut());
        if (isNumeric(highCut()) && Number(highCut()) > 0) config.high_cut = Number(highCut());
        if (filterLength() > 0) config.filter_length = filterLength();
        config.filter_type = filterType();
        config.window_type = windowType();

        config.with_response_spectrum = withResponseSpectrum();
        if (isNumeric(dampingRatio()) && Number(dampingRatio()) > 0) config.damping_ratio = Number(dampingRatio());
        if (isNumeric(periodStep()) && Number(periodStep()) > 0) config.period_step = Number(periodStep());
        if (isNumeric(periodEnd()) && Number(periodEnd()) > 0) config.period_end = Number(periodEnd());

        try {
            setProcessed(await process_api(currentRecord(), config));
        } catch (e) {
            clear();
            setError((e as Error).message);
        }

        setLoading(false);
    }

    onMount(() => {
        tippy(`#btn-process`, {
            content: "Process the record with the current settings.",
            animation: "scale",
        });
        tippy(`#btn-reset`, {
            content: "Clear the current settings.",
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
                    flexWrap: "wrap",
                    gap: "1rem",
                }}
            >
                <TextField label="ID" value={currentRecord()} defaultValue={currentRecord()} />
                <FormControlLabel
                    control={
                        <Checkbox
                            checked={withSpectrum()}
                            onChange={(_, checked) => {
                                setWithSpectrum(checked);
                                resizePlot();
                            }}
                        />
                    }
                    label="Compute Frequency Spectrum"
                />
                <FormControlLabel
                    control={
                        <Checkbox
                            checked={withFilter()}
                            onChange={(_, value) => {
                                setWithFilter(value);
                                resizePlot();
                            }}
                        />
                    }
                    label="Apply Filter"
                />
                <TextField
                    label="Upsampling Ratio"
                    type="number"
                    value={ratio() > 0 ? ratio() : ""}
                    defaultValue={ratio() > 0 ? ratio() : ""}
                    onChange={(_, value) => setRatio(Math.max(0, Math.round(Number(value))))}
                />
                <TextField
                    label="Filter Length"
                    type="number"
                    value={filterLength() > 0 ? filterLength() : ""}
                    defaultValue={filterLength() > 0 ? filterLength() : ""}
                    onChange={(_, value) => setFilterLength(Math.max(0, Math.round(Number(value))))}
                />
                <TextField
                    error={ifError(lowCut())}
                    label="Low Cut"
                    type="number"
                    value={lowCut()}
                    defaultValue={lowCut()}
                    onChange={(_, value) => setLowCut(value)}
                />
                <TextField
                    error={ifError(highCut())}
                    label="High Cut"
                    type="number"
                    value={highCut()}
                    defaultValue={highCut()}
                    onChange={(_, value) => setHighCut(value)}
                />
                <FormControl sx={{ minWidth: "14ch" }}>
                    <InputLabel>Filter Type</InputLabel>
                    <Select label="Filter Type" value={filterType()} onChange={(e) => setFilterType(e.target.value)}>
                        <MenuItem value="lowpass">Lowpass</MenuItem>
                        <MenuItem value="highpass">Highpass</MenuItem>
                        <MenuItem value="bandpass">Bandpass</MenuItem>
                    </Select>
                </FormControl>
                <FormControl sx={{ minWidth: "18ch" }}>
                    <InputLabel>Window Type</InputLabel>
                    <Select label="Window Type" value={windowType()} onChange={(e) => setWindowType(e.target.value)}>
                        <MenuItem value="flattop">FlatTop</MenuItem>
                        <MenuItem value="blackmanharris">BlackmanHarris</MenuItem>
                        <MenuItem value="nuttall">Nuttall</MenuItem>
                        <MenuItem value="hann">Hann</MenuItem>
                        <MenuItem value="hamming">Hamming</MenuItem>
                        <MenuItem value="kaiser">Kaiser</MenuItem>
                        <MenuItem value="chebwin">ChebWin</MenuItem>
                    </Select>
                </FormControl>
                <FormControlLabel
                    control={
                        <Checkbox
                            checked={withResponseSpectrum()}
                            onChange={(_, checked) => {
                                setWithResponseSpectrum(checked);
                                resizePlot();
                            }}
                        />
                    }
                    label="Compute Response Spectrum"
                />
                <TextField
                    error={ifError(dampingRatio())}
                    label="Damping Ratio"
                    type="number"
                    value={dampingRatio()}
                    defaultValue={dampingRatio()}
                    onChange={(_, value) => setDampingRatio(value)}
                />
                <TextField
                    error={ifError(periodStep())}
                    label="Period Step"
                    type="number"
                    value={periodStep()}
                    defaultValue={periodStep()}
                    onChange={(_, value) => setPeriodStep(value)}
                />
                <TextField
                    error={ifError(periodEnd())}
                    label="Period End"
                    type="number"
                    value={periodEnd()}
                    defaultValue={periodEnd()}
                    onChange={(_, value) => setPeriodEnd(value)}
                />
                <ButtonGroup variant="outlined" orientation="vertical">
                    <Button onClick={process} id="btn-process" disabled={loading()}>
                        Process
                    </Button>
                    <Button onClick={clear} id="btn-reset" disabled={loading()}>
                        Reset
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

const Waveform: Component = () => {
    createEffect(async () => {
        if (loading()) return;

        await Plotly.newPlot(
            "time",
            [
                {
                    x: Array<number>(processed().waveform.length)
                        .fill(0)
                        .map((_, i) => i * processed().time_interval),
                    y: processed().waveform,
                    type: "scatter",
                    mode: "lines",
                    name: processed().id,
                },
            ],
            {
                title: processed().file_name,
                xaxis: {
                    title: "Time (s)",
                    autorange: true,
                    automargin: true,
                },
                yaxis: {
                    title: "Acceleration (cm/s^2)",
                    autorange: true,
                    automargin: true,
                },
                autosize: true,
            },
            { autosizable: true, responsive: true },
        );
    });

    return <Paper id="time" sx={{ border: "1px solid darkgrey", height: "80vh" }} />;
};

const FrequencySpectrum: Component = () => {
    createEffect(async () => {
        if (loading()) return;

        await Plotly.newPlot(
            "spectrum",
            [
                {
                    x: Array<number>(processed().spectrum.length)
                        .fill(0)
                        .map((_, i) => i * processed().frequency_interval),
                    y: processed().spectrum,
                    type: "scatter",
                    mode: "lines",
                    name: processed().id,
                },
            ],
            {
                title: processed().file_name,
                xaxis: {
                    title: "Frequency (Hz)",
                    autorange: true,
                    automargin: true,
                },
                yaxis: {
                    title: "Acceleration (cm/s^2)",
                    autorange: true,
                    automargin: true,
                },
                autosize: true,
            },
            { autosizable: true, responsive: true },
        );
    });

    return <Paper id="spectrum" sx={{ border: "1px solid darkgrey", height: "80vh" }} />;
};

const ResponseSpectrum: Component = () => {
    createEffect(async () => {
        if (loading()) return;

        await Plotly.newPlot(
            "a_spectrum",
            [
                {
                    x: processed().period,
                    y: processed().acceleration_spectrum,
                    type: "scatter",
                    mode: "lines",
                    name: processed().id,
                },
            ],
            {
                title: processed().file_name,
                xaxis: {
                    title: "Period (s)",
                    autorange: true,
                    automargin: true,
                },
                yaxis: {
                    title: "Acceleration (cm/s^2)",
                    autorange: true,
                    automargin: true,
                },
                autosize: true,
            },
            { autosizable: true, responsive: true },
        );

        await Plotly.newPlot(
            "v_spectrum",
            [
                {
                    x: processed().period,
                    y: processed().velocity_spectrum,
                    type: "scatter",
                    mode: "lines",
                    name: processed().id,
                },
            ],
            {
                title: processed().file_name,
                xaxis: {
                    title: "Period (s)",
                    autorange: true,
                    automargin: true,
                },
                yaxis: {
                    title: "Velocity (cm/s)",
                    autorange: true,
                    automargin: true,
                },
                autosize: true,
            },
            { autosizable: true, responsive: true },
        );

        await Plotly.newPlot(
            "u_spectrum",
            [
                {
                    x: processed().period,
                    y: processed().displacement_spectrum,
                    type: "scatter",
                    mode: "lines",
                    name: processed().id,
                },
            ],
            {
                title: processed().file_name,
                xaxis: {
                    title: "Period (s)",
                    autorange: true,
                    automargin: true,
                },
                yaxis: {
                    title: "Displacement (cm)",
                    autorange: true,
                    automargin: true,
                },
                autosize: true,
            },
            { autosizable: true, responsive: true },
        );
    });

    return (
        <For each={["u_spectrum", "v_spectrum", "a_spectrum"]}>
            {(item) => <Paper id={item} sx={{ border: "1px solid darkgrey", height: "80vh" }} />}
        </For>
    );
};
export default function Process() {
    return (
        <>
            <Grid item xs={12} md={12}>
                <Settings />
            </Grid>
            <Grid item xs={12} md={12} sx={{ display: "flex", gap: "1rem", flexDirection: "column" }}>
                {processed().waveform && <Waveform />}
                {withSpectrum() && processed().spectrum && <FrequencySpectrum />}
                {withResponseSpectrum() && processed().period && <ResponseSpectrum />}
            </Grid>
        </>
    );
}
