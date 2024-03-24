import { Component, createEffect, createMemo, createSignal, onMount } from "solid-js";
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
    Select,
    TextField,
} from "@suid/material";
import { process_api, ProcessConfig, ProcessResponse } from "./API";
import Plotly from "plotly.js-dist-min";

const [processed, setProcessed] = createSignal<ProcessResponse>({} as ProcessResponse);
const [error, setError] = createSignal("");
const [loading, setLoading] = createSignal(false);

const [withFilter, setWithFilter] = createSignal(false);
const [withSpectrum, setWithSpectrum] = createSignal(false);
const [withResponseSpectrum, setWithResponseSpectrum] = createSignal(false);

const [lowCut, setLowCut] = createSignal(0);
const [highCut, setHighCut] = createSignal(0);
const [ratio, setRatio] = createSignal(0);
const [filterLength, setFilterLength] = createSignal(0);
const [filterType, setFilterType] = createSignal("lowpass");
const [windowType, setWindowType] = createSignal("hann");

const Settings: Component = () => {
    const [currentRecord, setCurrentRecord] = createSignal("abf60c4d-ae35-4ec0-b63a-38362891cea7");

    function clear() {
        setProcessed({} as ProcessResponse);
    }

    async function process() {
        setLoading(true);

        let config = new ProcessConfig();
        if (ratio() > 0) config.ratio = ratio();
        if (lowCut() > 0) config.low_cut = lowCut();
        if (highCut() > 0) config.high_cut = highCut();
        if (filterLength() > 0) config.filter_length = filterLength();
        config.filter_type = filterType();
        config.window_type = windowType();

        config.with_filter = withFilter();
        config.with_spectrum = withSpectrum();
        config.with_response_spectrum = withResponseSpectrum();

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
                    gap: "1rem",
                }}
            >
                <TextField
                    label="ID"
                    value={currentRecord()}
                    defaultValue={currentRecord()}
                    InputProps={{ readOnly: true }}
                />
                <FormControlLabel
                    control={
                        <Checkbox
                            checked={withFilter()}
                            onChange={(_, value) => {
                                setWithFilter(value);
                            }}
                        />
                    }
                    label="Apply Filter"
                />
                <FormControlLabel
                    control={
                        <Checkbox
                            checked={withSpectrum()}
                            onChange={(_, checked) => {
                                setWithSpectrum(checked);
                            }}
                        />
                    }
                    label="Compute Frequency Spectrum"
                />
                <FormControlLabel
                    control={
                        <Checkbox
                            checked={withResponseSpectrum()}
                            onChange={(_, checked) => {
                                setWithResponseSpectrum(checked);
                            }}
                        />
                    }
                    label="Compute Response Spectrum"
                />
                <TextField
                    label="Ratio"
                    type="number"
                    value={ratio() > 0 ? ratio() : ""}
                    defaultValue={ratio() > 0 ? ratio() : ""}
                    onChange={(_, value) => setRatio(Math.max(0, Number(value)))}
                />
                <TextField
                    label="Filter Length"
                    type="number"
                    value={filterLength() > 0 ? filterLength() : ""}
                    defaultValue={filterLength() > 0 ? filterLength() : ""}
                    onChange={(_, value) => setFilterLength(Math.max(0, Number(value)))}
                />
                <TextField
                    label="Low Cut"
                    type="number"
                    value={lowCut() > 0 ? lowCut() : ""}
                    defaultValue={lowCut() > 0 ? lowCut() : ""}
                    onChange={(_, value) => setLowCut(Math.max(0, Number(value)))}
                />
                <TextField
                    label="High Cut"
                    type="number"
                    value={highCut() > 0 ? highCut() : ""}
                    defaultValue={highCut() > 0 ? highCut() : ""}
                    onChange={(_, value) => setHighCut(Math.max(0, Number(value)))}
                />
                <FormControl>
                    <InputLabel>Filter Type</InputLabel>
                    <Select value={filterType()} onChange={(e) => setFilterType(e.target.value)}>
                        <MenuItem value="lowpass">Lowpass</MenuItem>
                        <MenuItem value="highpass">Highpass</MenuItem>
                        <MenuItem value="bandpass">Bandpass</MenuItem>
                    </Select>
                </FormControl>
                <FormControl>
                    <InputLabel>Window Type</InputLabel>
                    <Select autoWidth value={windowType()} onChange={(e) => setWindowType(e.target.value)}>
                        <MenuItem value="flattop">FlatTop</MenuItem>
                        <MenuItem value="blackmanharris">BlackmanHarris</MenuItem>
                        <MenuItem value="nuttall">Nuttall</MenuItem>
                        <MenuItem value="hann">Hann</MenuItem>
                        <MenuItem value="hamming">Hamming</MenuItem>
                        <MenuItem value="kaiser">Kaiser</MenuItem>
                        <MenuItem value="chebwin">ChebWin</MenuItem>
                    </Select>
                </FormControl>
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

    return (
        <Card sx={{ border: "1px solid darkgrey", height: "80vh" }}>
            <CardContent id="time" sx={{ height: "100%" }} />
        </Card>
    );
};

const Spectrum: Component = () => {
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

    return (
        <Card sx={{ border: "1px solid darkgrey", height: "80vh" }}>
            <CardContent id="spectrum" sx={{ height: "100%" }} />
        </Card>
    );
};

export default function Process() {
    const waveform_width = createMemo(() => 12 / (1 + Number(withSpectrum()) + Number(withResponseSpectrum())));
    const spectrum_width = createMemo(() => 12 / (2 + Number(withResponseSpectrum())));
    const response_spectrum_width = createMemo(() => 12 / (2 + Number(withSpectrum())));

    return (
        <>
            <Grid item xs={12} md={12}>
                <Settings />
            </Grid>
            {processed().waveform && (
                <Grid item xs={12} md={waveform_width()}>
                    <Waveform />
                </Grid>
            )}
            {withSpectrum() && processed().spectrum && (
                <Grid item xs={12} md={spectrum_width()}>
                    <Spectrum />
                </Grid>
            )}
        </>
    );
}
