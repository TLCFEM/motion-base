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
    InputLabel,
    LinearProgress,
    MenuItem,
    Modal,
    Paper,
    Select,
    Stack,
    TextField,
} from "@suid/material";
import { ifError, isNumeric, process_api, ProcessConfig, ProcessResponse, sxProps } from "./API";
import Plotly from "plotly.js-dist-min";

const [processed, setProcessed] = createSignal<ProcessResponse>({} as ProcessResponse);
const [error, setError] = createSignal("");
const [loading, setLoading] = createSignal(false);

const [withWaveform, setWithWaveform] = createSignal(true);
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

const Settings: Component<sxProps> = (props) => {
    const [currentRecord, setCurrentRecord] = createSignal("");

    function download() {
        if (processed() && processed().id) {
            const element = document.createElement("a");
            const file = new Blob([JSON.stringify(processed())], { type: "application/json" });
            element.href = URL.createObjectURL(file);
            element.download = `${processed().id}.json`;
            document.body.appendChild(element); // Required for this to work in FireFox
            element.click();
        }
    }

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
            // clear();
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
        tippy(`#btn-download`, {
            content: "Download the processed record in json.",
            animation: "scale",
        });
    });

    return (
        <Card>
            <CardContent
                sx={{
                    ...props.sx,
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "center",
                    alignContent: "center",
                    alignItems: "flex-start",
                    gap: "1rem",
                }}
            >
                <Box
                    sx={{
                        display: "flex",
                        justifyContent: "center",
                        alignContent: "center",
                        alignItems: "center",
                        gap: "1rem",
                    }}
                >
                    <FormControlLabel
                        control={
                            <Checkbox checked={withWaveform()} onChange={(_, checked) => setWithWaveform(checked)} />
                        }
                        label="Show Waveform"
                    />
                    <FormControlLabel
                        control={
                            <Checkbox checked={withSpectrum()} onChange={(_, checked) => setWithSpectrum(checked)} />
                        }
                        label="Compute Frequency Spectrum"
                    />
                    <TextField
                        label="ID"
                        value={currentRecord()}
                        defaultValue={currentRecord()}
                        onChange={(_, value) => setCurrentRecord(value)}
                    />
                    <ButtonGroup variant="outlined" orientation="horizontal">
                        <Button onClick={process} id="btn-process" disabled={loading()}>
                            Process
                        </Button>
                        <Button onClick={clear} id="btn-reset" disabled={loading()}>
                            Reset
                        </Button>
                        <Button onClick={download} id="btn-download" disabled={loading()}>
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
                </Box>
                <Box
                    sx={{
                        display: "flex",
                        justifyContent: "center",
                        alignContent: "center",
                        alignItems: "center",
                        gap: "1rem",
                    }}
                >
                    <FormControlLabel
                        control={<Checkbox checked={withFilter()} onChange={(_, value) => setWithFilter(value)} />}
                        label="Apply Filter"
                    />
                    <TextField
                        label="Upsampling Ratio"
                        type="number"
                        value={ratio() > 0 ? ratio() : ""}
                        defaultValue={ratio() > 0 ? ratio() : ""}
                        onChange={(_, value) => setRatio(Math.max(0, Math.round(Number(value))))}
                        disabled={!withFilter()}
                    />
                    <TextField
                        label="Filter Length"
                        type="number"
                        value={filterLength() > 0 ? filterLength() : ""}
                        defaultValue={filterLength() > 0 ? filterLength() : ""}
                        onChange={(_, value) => setFilterLength(Math.max(0, Math.round(Number(value))))}
                        disabled={!withFilter()}
                    />
                    <TextField
                        error={ifError(lowCut())}
                        label="Low Cut"
                        type="number"
                        value={lowCut()}
                        defaultValue={lowCut()}
                        onChange={(_, value) => setLowCut(value)}
                        disabled={!withFilter() || filterType() === "lowpass"}
                    />
                    <TextField
                        error={ifError(highCut())}
                        label="High Cut"
                        type="number"
                        value={highCut()}
                        defaultValue={highCut()}
                        onChange={(_, value) => setHighCut(value)}
                        disabled={!withFilter() || filterType() === "highpass"}
                    />
                    <FormControl sx={{ minWidth: "14ch" }} disabled={!withFilter()}>
                        <InputLabel>Filter Type</InputLabel>
                        <Select
                            label="Filter Type"
                            value={filterType()}
                            onChange={(e) => setFilterType(e.target.value)}
                        >
                            <MenuItem value="lowpass">Lowpass</MenuItem>
                            <MenuItem value="highpass">Highpass</MenuItem>
                            <MenuItem value="bandpass">Bandpass</MenuItem>
                        </Select>
                    </FormControl>
                    <FormControl sx={{ minWidth: "18ch" }} disabled={!withFilter()}>
                        <InputLabel>Window Type</InputLabel>
                        <Select
                            label="Window Type"
                            value={windowType()}
                            onChange={(e) => setWindowType(e.target.value)}
                        >
                            <MenuItem value="flattop">FlatTop</MenuItem>
                            <MenuItem value="blackmanharris">BlackmanHarris</MenuItem>
                            <MenuItem value="nuttall">Nuttall</MenuItem>
                            <MenuItem value="hann">Hann</MenuItem>
                            <MenuItem value="hamming">Hamming</MenuItem>
                            <MenuItem value="kaiser">Kaiser</MenuItem>
                            <MenuItem value="chebwin">ChebWin</MenuItem>
                        </Select>
                    </FormControl>
                </Box>
                <Box
                    sx={{
                        display: "flex",
                        justifyContent: "center",
                        alignContent: "center",
                        alignItems: "center",
                        gap: "1rem",
                    }}
                >
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
                        disabled={!withResponseSpectrum()}
                    />
                    <TextField
                        error={ifError(periodStep())}
                        label="Period Step"
                        type="number"
                        value={periodStep()}
                        defaultValue={periodStep()}
                        onChange={(_, value) => setPeriodStep(value)}
                        disabled={!withResponseSpectrum()}
                    />
                    <TextField
                        error={ifError(periodEnd())}
                        label="Period End"
                        type="number"
                        value={periodEnd()}
                        defaultValue={periodEnd()}
                        onChange={(_, value) => setPeriodEnd(value)}
                        disabled={!withResponseSpectrum()}
                    />
                </Box>
            </CardContent>
            <Box sx={{ width: "100%" }}>
                {loading() ? <LinearProgress /> : <LinearProgress variant="determinate" value={0} />}
            </Box>
        </Card>
    );
};

const Waveform: Component<sxProps> = (props) => {
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

    return <Paper id="time" sx={props.sx} />;
};

const FrequencySpectrum: Component<sxProps> = (props) => {
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

    return <Paper id="spectrum" sx={props.sx} />;
};

const ResponseSpectrum: Component<sxProps> = (props) => {
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

    return <For each={["a_spectrum", "v_spectrum", "u_spectrum"]}>{(item) => <Paper id={item} sx={props.sx} />}</For>;
};

const Process: Component<sxProps> = (props) => {
    return (
        <Stack sx={{ gap: "1rem" }}>
            <Settings sx={props.sx} />
            {withWaveform() && processed().waveform && <Waveform sx={{ ...props.sx, height: "70vh" }} />}
            {withSpectrum() && processed().spectrum && <FrequencySpectrum sx={{ ...props.sx, height: "70vh" }} />}
            {withResponseSpectrum() && processed().period && <ResponseSpectrum sx={{ ...props.sx, height: "70vh" }} />}
        </Stack>
    );
};

export default Process;
