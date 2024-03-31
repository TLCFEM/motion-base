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
import { createDownloadLink, ifError, isNumeric, process_api, ProcessConfig, ProcessResponse, sxProps } from "./API";
import Plotly from "plotly.js-dist-min";

const [processed, setProcessed] = createSignal<ProcessResponse>({} as ProcessResponse);
const [error, setError] = createSignal("");
const [loading, setLoading] = createSignal(false);

const [currentRecord, setCurrentRecord] = createSignal("");
const [normalised, setNormalised] = createSignal(false);

const [withWaveform, setWithWaveform] = createSignal(true);
const [withFilter, setWithFilter] = createSignal(false);
const [withSpectrum, setWithSpectrum] = createSignal(false);
const [withResponseSpectrum, setWithResponseSpectrum] = createSignal(false);

const [lowCut, setLowCut] = createSignal("");
const [highCut, setHighCut] = createSignal("");
const [upRatio, setUpRatio] = createSignal(0);
const [downRatio, setDownRatio] = createSignal(0);
const [filterLength, setFilterLength] = createSignal(0);
const [filterType, setFilterType] = createSignal("lowpass");
const [windowType, setWindowType] = createSignal("hann");

const [dampingRatio, setDampingRatio] = createSignal("");
const [periodStep, setPeriodStep] = createSignal("");
const [periodEnd, setPeriodEnd] = createSignal("");

const [removeHead, setRemoveHead] = createSignal("");

const Settings: Component<sxProps> = (props) => {
    function clear() {
        setNormalised(false);

        setWithFilter(false);
        setWithSpectrum(false);
        setWithResponseSpectrum(false);

        setLowCut("");
        setHighCut("");
        setUpRatio(0);
        setDownRatio(0);
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

        if (normalised()) config.normalised = normalised();

        config.with_spectrum = withSpectrum();

        config.with_filter = withFilter();
        if (upRatio() > 1) config.up_ratio = upRatio();
        if (downRatio() > 1) config.down_ratio = downRatio();
        if (isNumeric(lowCut()) && Number(lowCut()) > 0) config.low_cut = Number(lowCut());
        if (isNumeric(highCut()) && Number(highCut()) > 0) config.high_cut = Number(highCut());
        if (filterLength() > 8) config.filter_length = filterLength();
        config.filter_type = filterType();
        config.window_type = windowType();

        config.with_response_spectrum = withResponseSpectrum();
        if (isNumeric(dampingRatio()) && Number(dampingRatio()) > 0) config.damping_ratio = Number(dampingRatio());
        if (isNumeric(periodStep()) && Number(periodStep()) > 0) config.period_step = Number(periodStep());
        if (isNumeric(periodEnd()) && Number(periodEnd()) > 0) config.period_end = Number(periodEnd());

        if (isNumeric(removeHead()) && Number(removeHead()) > 0) config.remove_head = Number(removeHead());

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
        tippy(`#remove-head`, {
            content: "Remove the first a few seconds, default is zero.",
            animation: "scale",
        });
        tippy(`#upsampling-ratio`, {
            content: "Assign a positive integer to upsample the record, default is one (no upsampling).",
            animation: "scale",
        });
        tippy(`#downsampling-ratio`, {
            content: "Assign a positive integer to downsample the record, default is one (no downsampling).",
            animation: "scale",
        });
        tippy(`#filter-length`, {
            content: "Assign a positive integer (at least eight) to set the filter window length, default is 16.",
            animation: "scale",
        });
        tippy(`#low-cut`, {
            content: "The low-cut frequency for the highpass and bandpass filters, default is 0.05.",
            animation: "scale",
        });
        tippy(`#high-cut`, {
            content: "The high-cut frequency for the lowpass and bandpass filters, default is 40.0.",
            animation: "scale",
        });
        tippy(`#damping-ratio`, {
            content: "Assign a positive floating point number representing the damping ratio, default is 0.05.",
            animation: "scale",
        });
        tippy(`#period-step`, {
            content: "The period interval for the response spectrum computation, default is 0.05.",
            animation: "scale",
        });
        tippy(`#period-end`, {
            content: "The termination period (right bound) for the response spectrum computation, default is 20.",
            animation: "scale",
        });
        tippy(`#chk-waveform`, {
            content: "Display the original waveform.",
            animation: "scale",
        });
        tippy(`#chk-normalised`, {
            content: "Normalise the PGA to unity.",
            animation: "scale",
        });
        tippy(`#chk-frequency-spectrum`, {
            content: "Compute the frequency spectrum of the original waveform.",
            animation: "scale",
        });
        tippy(`#chk-filter`, {
            content: "Further process the record by applying a filter.",
            animation: "scale",
        });
        tippy(`#chk-response-spectrum`, {
            content: "Compute response spectra of the original waveform.",
            animation: "scale",
        });
    });

    return (
        <Card sx={props.sx}>
            <CardContent
                sx={{
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
                        id="chk-waveform"
                        name="chk-waveform"
                        label="Waveform"
                        control={
                            <Checkbox checked={withWaveform()} onChange={(_, checked) => setWithWaveform(checked)} />
                        }
                    />
                    <FormControlLabel
                        id="chk-normalised"
                        name="chk-normalised"
                        label="Normalised"
                        control={<Checkbox checked={normalised()} onChange={(_, checked) => setNormalised(checked)} />}
                    />
                    <FormControlLabel
                        id="chk-frequency-spectrum"
                        name="chk-frequency-spectrum"
                        label="Frequency Spectrum"
                        control={
                            <Checkbox checked={withSpectrum()} onChange={(_, checked) => setWithSpectrum(checked)} />
                        }
                    />
                    <TextField
                        id="record-id"
                        sx={{ minWidth: "36ch" }}
                        label="ID"
                        value={currentRecord()}
                        onChange={(_, value) => setCurrentRecord(value)}
                    />
                    <TextField
                        id="remove-head"
                        error={ifError(removeHead())}
                        label="Remove Head (s)"
                        type="number"
                        value={removeHead()}
                        onChange={(_, value) => setRemoveHead(value)}
                    />
                    <ButtonGroup variant="contained" orientation="horizontal">
                        <Button onClick={process} id="btn-process" disabled={loading()}>
                            Process
                        </Button>
                        <Button onClick={clear} id="btn-reset" disabled={loading()}>
                            Reset
                        </Button>
                        <Button
                            onClick={() => {
                                const element = createDownloadLink(processed());
                                element.download = `${processed().id}.json`;
                                document.body.appendChild(element); // Required for this to work in FireFox
                                element.click();
                            }}
                            id="btn-download"
                            disabled={loading() || !processed().id}
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
                        id="chk-filter"
                        name="chk-filter"
                        label="Apply Filter"
                        control={<Checkbox checked={withFilter()} onChange={(_, value) => setWithFilter(value)} />}
                    />
                    <TextField
                        id="upsampling-ratio"
                        label="Upsampling"
                        type="number"
                        value={upRatio() > 0 ? upRatio() : ""}
                        onChange={(_, value) => setUpRatio(Math.max(0, Math.round(Number(value))))}
                        disabled={!withFilter()}
                        sx={{ maxWidth: "10rem" }}
                    />
                    <TextField
                        id="downsampling-ratio"
                        label="Downsampling"
                        type="number"
                        value={downRatio() > 0 ? downRatio() : ""}
                        onChange={(_, value) => setDownRatio(Math.max(0, Math.round(Number(value))))}
                        disabled={!withFilter()}
                        sx={{ maxWidth: "10rem" }}
                    />
                    <TextField
                        id="filter-length"
                        label="Filter Length"
                        type="number"
                        value={filterLength() > 0 ? filterLength() : ""}
                        onChange={(_, value) => setFilterLength(Math.max(0, Math.round(Number(value))))}
                        disabled={!withFilter()}
                        sx={{ maxWidth: "10rem" }}
                    />
                    <TextField
                        id="low-cut"
                        error={ifError(lowCut())}
                        label="Low Cut"
                        type="number"
                        value={lowCut()}
                        onChange={(_, value) => setLowCut(value)}
                        disabled={!withFilter() || filterType() === "lowpass"}
                        sx={{ maxWidth: "10rem" }}
                    />
                    <TextField
                        id="high-cut"
                        error={ifError(highCut())}
                        label="High Cut"
                        type="number"
                        value={highCut()}
                        onChange={(_, value) => setHighCut(value)}
                        disabled={!withFilter() || filterType() === "highpass"}
                        sx={{ maxWidth: "10rem" }}
                    />
                    <FormControl sx={{ minWidth: "14ch" }} disabled={!withFilter()}>
                        <InputLabel>Filter Type</InputLabel>
                        <Select
                            id="select-filter"
                            name="select-filter"
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
                            id="select-window"
                            name="select-window"
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
                        id="chk-response-spectrum"
                        name="chk-response-spectrum"
                        label="Compute Response Spectrum"
                        control={
                            <Checkbox
                                checked={withResponseSpectrum()}
                                onChange={(_, checked) => {
                                    setWithResponseSpectrum(checked);
                                }}
                            />
                        }
                    />
                    <TextField
                        id="damping-ratio"
                        error={ifError(dampingRatio())}
                        label="Damping Ratio"
                        type="number"
                        value={dampingRatio()}
                        onChange={(_, value) => setDampingRatio(value)}
                        disabled={!withResponseSpectrum()}
                        sx={{ maxWidth: "10rem" }}
                    />
                    <TextField
                        id="period-step"
                        error={ifError(periodStep())}
                        label="Period Step"
                        type="number"
                        value={periodStep()}
                        onChange={(_, value) => setPeriodStep(value)}
                        disabled={!withResponseSpectrum()}
                        sx={{ maxWidth: "10rem" }}
                    />
                    <TextField
                        id="period-end"
                        error={ifError(periodEnd())}
                        label="Period End"
                        type="number"
                        value={periodEnd()}
                        onChange={(_, value) => setPeriodEnd(value)}
                        disabled={!withResponseSpectrum()}
                        sx={{ maxWidth: "10rem" }}
                    />
                </Box>
            </CardContent>
            {loading() ? <LinearProgress /> : <LinearProgress variant="determinate" value={0} />}
        </Card>
    );
};

const Waveform: Component<sxProps> = (props) => {
    createEffect(async () => {
        if (loading() || !processed().waveform) return;

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
        if (loading() || !withSpectrum()) return;

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
        if (loading() || !withResponseSpectrum()) return;

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
        <Stack sx={{ gap: "1rem", flexGrow: 1 }}>
            <Settings sx={props.sx} />
            {withWaveform() && processed().waveform && <Waveform sx={{ ...props.sx, height: "70vh" }} />}
            {withSpectrum() && processed().spectrum && <FrequencySpectrum sx={{ ...props.sx, height: "70vh" }} />}
            {withResponseSpectrum() && processed().period && <ResponseSpectrum sx={{ ...props.sx, height: "70vh" }} />}
        </Stack>
    );
};

export default Process;
