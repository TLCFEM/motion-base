import {Component, createEffect, createSignal, onMount} from "solid-js"
import {axis_label, Record} from "./Utility"
// @ts-ignore
import Plotly from 'plotly.js-dist-min'
import Grid from "@suid/material/Grid"
import TextField from "@suid/material/TextField"
import Button from "@suid/material/Button"
import SearchIcon from "@suid/icons-material/Search"
// @ts-ignore
import * as ST from '@suid/types'
import Stack from "@suid/material/Stack"
import axios from "./API";
import Switch from "@suid/material/Switch";
import {ResponseSpectrum} from "./ResponseSpectrum";
import Card from "@suid/material/Card";
// @ts-ignore
import {validate as uuidValidate} from 'uuid';
import tippy from "tippy.js";

const [record_id, set_record_id] = createSignal('')
const [upsampling_rate, set_upsampling_rate] = createSignal(1)
const [filter_length, set_filter_length] = createSignal(32)
const [filter_type, set_filter_type] = createSignal('bandpass')
const [window_type, set_window_type] = createSignal('nuttall')
const [region, set_region] = createSignal('jp')
const [low_cut, set_low_cut] = createSignal(0.1)
const [high_cut, set_high_cut] = createSignal(10)

const [show_waveform, set_show_waveform] = createSignal(true)
const [show_spectrum, set_show_spectrum] = createSignal(false)
const [show_response_spectrum, set_show_response_spectrum] = createSignal(false)

const [original_record, set_original_record] = createSignal<Record>(new Record({}))
const [processed_record, set_processed_record] = createSignal<Record>(new Record({}))

async function fetch() {
    const url = `/process?record_id=${record_id()}`
    let query_data = {with_filter: false}
    // @ts-ignore
    if (show_spectrum()) query_data['with_spectrum'] = true
    // @ts-ignore
    if (show_response_spectrum()) query_data['with_response_spectrum'] = true
    await axios.post(url, query_data).then(
        res => set_original_record(new Record(res.data))
    )

    query_data.with_filter = filter_type() !== ''
    // @ts-ignore
    if (upsampling_rate()) query_data['ratio'] = upsampling_rate()
    // @ts-ignore
    if (filter_length()) query_data['filter_length'] = filter_length()
    // @ts-ignore
    if (low_cut()) query_data['low_cut'] = low_cut()
    // @ts-ignore
    if (high_cut()) query_data['high_cut'] = high_cut()
    // @ts-ignore
    if (show_spectrum()) query_data['with_spectrum'] = true
    // @ts-ignore
    if (show_response_spectrum()) query_data['with_response_spectrum'] = true
    await axios.post(url, query_data).then(
        res => set_processed_record(new Record(res.data))
    )
}

const RecordID = () => {
    onMount(() => {
        tippy('#record-id', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'The UUID of the record.',
        })
    })

    const [error, set_error] = createSignal(false)

    const handleChange = (event: any) => {
        const value = event.target.value
        set_error(!uuidValidate(value))
        set_record_id(value)
    }

    return <TextField InputLabelProps={{shrink: true}} id='record-id' label='Record ID' type='text' value={record_id()}
                      error={error()} sx={{width: '400px'}} onChange={handleChange}/>
}

const FilterLength = () => {
    onMount(() => {
        tippy('#filter-length', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'Half of the filter order, the exact filter length is twice of this value plus one.',
        })
    })

    const [error, set_error] = createSignal(false)

    const handleChange = (event: any) => {
        const re: RegExp = /^\d+$/
        const value = event.target.value
        set_error(!value.match(re))
        set_filter_length(value)
    }

    return <TextField InputLabelProps={{shrink: true}} id='filter-length' label='Filter Length' type='text'
                      value={filter_length()} error={error()} onChange={handleChange}/>
}

const FilterType = () => {
    onMount(() => {
        tippy('#filter-type', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'Any of lowpass, highpass, bandpass, bandstop, or empty to disable filtering.',
        })
    })

    const [error, set_error] = createSignal(false)

    const handleChange = (event: any) => {
        const re: RegExp = /^(lowpass|highpass|bandpass|bandstop)$/
        const value = event.target.value.toLowerCase()
        if (value !== '') set_error(!value.match(re))
        set_filter_type(value)
    }

    return <TextField InputLabelProps={{shrink: true}} id='filter-type' label='Filter Type' type='text'
                      value={filter_type()} error={error()} onChange={handleChange}/>
}

const WindowType = () => {
    onMount(() => {
        tippy('#window-type', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'Any of flattop, blackmanharris, nuttall, hann, hamming, kaiser or chebwin.',
        })
    })

    const [error, set_error] = createSignal(false)

    const handleChange = (event: any) => {
        const re: RegExp = /^(flattop|blackmanharris|nuttall|hann|hamming|kaiser|chebwin)$/
        const value = event.target.value.toLowerCase()
        set_error(!value.match(re))
        set_window_type(value)
    }

    return <TextField InputLabelProps={{shrink: true}} id='filter-type' label='Filter Type' type='text'
                      value={window_type()} error={error()} onChange={handleChange}/>
}

const UpsamplingRate = () => {
    onMount(() => {
        tippy('#upsampling-rate', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'The upsampling rate, an integer at least 1.',
        })
    })

    const [error, set_error] = createSignal(false)

    const handleChange = (event: any) => {
        const re: RegExp = /^\d+$/
        const value = event.target.value
        set_error(!value.match(re))
        set_upsampling_rate(value)
    }

    return <TextField InputLabelProps={{shrink: true}} id='upsampling-rate' label='Upsampling Rate' type='text'
                      value={upsampling_rate()} error={error()} onChange={handleChange}/>
}

const LowCut = () => {
    onMount(() => {
        tippy('#low-cut', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'The lower cutoff frequency in Hz.',
        })
    })

    const [error, set_error] = createSignal(false)

    const handleChange = (event: any) => {
        const re: RegExp = /^\d+(\.\d{1,2})?$/
        const value = event.target.value
        set_error(!value.match(re))
        set_low_cut(value)
    }

    return <TextField InputLabelProps={{shrink: true}} id='low-cut' label='Low Cut' type='text'
                      value={low_cut()} error={error()} onChange={handleChange}/>
}

const HighCut = () => {
    onMount(() => {
        tippy('#high-cut', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'The higher cutoff frequency in Hz.',
        })
    })

    const [error, set_error] = createSignal(false)

    const handleChange = (event: any) => {
        const re: RegExp = /^\d+(\.\d{1,2})?$/
        const value = event.target.value
        set_error(!value.match(re))
        set_high_cut(value)
    }

    return <TextField InputLabelProps={{shrink: true}} id='high-cut' label='High Cut' type='text'
                      value={high_cut()} error={error()} onChange={handleChange}/>
}

const MainCanvas = () => {
    createEffect(() => {
        Plotly.react(document.getElementById('main_canvas'),
            [
                original_record().extract_waveform('original'),
                processed_record().extract_waveform('processed')
            ],
            {
                autosize: true,
                automargin: true,
                title: {text: record_id(), font: {size: 20},},
                xaxis: axis_label('Time (s)', 14),
                yaxis: axis_label('Amplitude (Gal)', 14),
                showlegend: true,
                legend: {
                    x: 1,
                    xanchor: 'right',
                    y: 1
                }
            }, {responsive: true})
    })

    return <Card id='main_canvas'></Card>
}

const SpectrumCanvas = () => {
    createEffect(() => {
        Plotly.react(document.getElementById('spectrum_canvas'),
            [
                original_record().extract_spectrum('original'),
                processed_record().extract_spectrum('processed'),
            ],
            {
                autosize: true,
                margin: {l: 60, r: 60, b: 60, t: 60, pad: 0},
                automargin: true,
                title: {text: 'DFT', font: {size: 14},},
                xaxis: axis_label('Frequency (Hz)', 12),
                yaxis: axis_label('Amplitude (Gal)', 12),
                showlegend: true,
                legend: {
                    x: 1,
                    xanchor: 'right',
                    y: 1
                }
            }, {responsive: true})
    })

    return <Card id='spectrum_canvas'></Card>
}

const ProcessPage: Component = () => {
    onMount(() => {
        tippy('#show_waveform', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'Show Waveform!',
        })

        tippy('#show_spectrum', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'Show Spectrum!',
        })

        tippy('#show_response_spectrum', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'Show Response Spectrum!',
        })
    })

    const response_spectrum_width = () => show_waveform() ? show_spectrum() ? 3 : 4 : 4

    return <Grid container xs={12} spacing={2}>
        <Grid item xs={12}>
            <Stack component='form' alignContent='center' justifyContent='center' alignItems='center'
                   direction='row' spacing={1}>
                <RecordID/>
                <FilterLength/>
                <FilterType/>
                <WindowType/>
                <UpsamplingRate/>
                <LowCut/>
                <HighCut/>
                <Button variant='contained' id='process' onClick={fetch}>
                    <SearchIcon/>
                </Button>
                <Switch id='show_waveform' checked={show_waveform()}
                        onChange={() => set_show_waveform(!show_waveform())}/>
                <Switch id='show_spectrum' checked={show_spectrum()}
                        onChange={() => set_show_spectrum(!show_spectrum())}/>
                <Switch id='show_response_spectrum' checked={show_response_spectrum()}
                        onChange={() => set_show_response_spectrum(!show_response_spectrum())}/>
            </Stack>
        </Grid>
        {show_waveform() ? <Grid item xs={12}><MainCanvas/></Grid> : null}
        <Grid container item xs={12} spacing={2}>
            {show_spectrum()
                ? <Grid item xs={show_waveform() ? show_response_spectrum() ? 3 : 12 : 12}>
                    <SpectrumCanvas/>
                </Grid>
                : null}
            {show_response_spectrum()
                ? <Grid item xs={response_spectrum_width()}>{ResponseSpectrum([
                    original_record().extract_response_spectrum('original', 'SA'),
                    processed_record().extract_response_spectrum('processed', 'SA')
                ], 'SA', 'sa_canvas')}</Grid>
                : null}
            {show_response_spectrum()
                ? <Grid item xs={response_spectrum_width()}>{ResponseSpectrum([
                    original_record().extract_response_spectrum('original', 'SV'),
                    processed_record().extract_response_spectrum('processed', 'SV')
                ], 'SV', 'sv_canvas')}</Grid>
                : null}
            {show_response_spectrum()
                ? <Grid item xs={response_spectrum_width()}>{ResponseSpectrum([
                    original_record().extract_response_spectrum('original', 'SD'),
                    processed_record().extract_response_spectrum('processed', 'SD')
                ], 'SD', 'sd_canvas')}</Grid>
                : null}
        </Grid>
    </Grid>
}

export default ProcessPage