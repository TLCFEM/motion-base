import {Component, createEffect, createSignal} from "solid-js"
import {axis_label, Record, set_response_spectrum} from "./Utility"
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

const [record, set_record] = createSignal<Record>(new Record({}))

const [record_id, set_record_id] = createSignal('')
const [upsampling_rate, set_upsampling_rate] = createSignal(1)
const [filter_length, set_filter_length] = createSignal(32)
const [filter_type, set_filter_type] = createSignal('bandpass')
const [region, set_region] = createSignal('jp')
const [low_cut, set_low_cut] = createSignal(0.1)
const [high_cut, set_high_cut] = createSignal(10)

const [show_spectrum, set_show_spectrum] = createSignal(false)
const [show_response_spectrum, set_show_response_spectrum] = createSignal(false)

async function fetch() {
    let url = `/${region()}/waveform/${record_id()}`
    let new_record: Record = new Record({})
    await axios.get(url).then(
        res => new_record = new Record(res.data)
    )

    if (show_spectrum()) {
        url = `/${region()}/spectrum/${record_id()}`
        await axios.get(url).then(
            res => {
                new_record.frequency_interval = res.data.interval
                new_record.spectrum = res.data.data
            }
        )
    }

    if (show_response_spectrum()) {
        url = `/${region()}/response_spectrum/${record_id()}`
        await axios.get(url).then(
            res => set_response_spectrum(new_record, res.data.data)
        )
    }

    url = `/${region()}/process?record_id=${record_id()}`
    if (upsampling_rate()) url += `&upsampling_rate=${upsampling_rate()}`
    if (filter_length()) url += `&filter_length=${filter_length()}`
    if (high_cut()) url += `&high_cut=${high_cut()}`
    url += '&with_spectrum=true'
    await axios.post(url).then(
        res => {
            new_record.upsampled_time_interval = res.data.time_interval
            new_record.upsampled_waveform = res.data.waveform
            new_record.upsampled_frequency_interval = res.data.frequency_interval
            new_record.upsampled_spectrum = res.data.spectrum
        }
    )

    set_record(new_record)
}

function ProcessConfig() {
    return <Stack component='form' noValidate alignContent='center' justifyContent='center' alignItems='center'
                  direction='row' spacing={2} autocomplete='off'>
        <TextField id='record-id' label='Record ID' type='text' value={record_id()} sx={{width: '400px'}}
                   onChange={(event) => (set_record_id(event.target.value))}/>
        <TextField id='filter_length' label='Filter Length' type='number' value={filter_length()}
                   onChange={(event) => (set_filter_length(Number(event.target.value)))}/>
        <TextField id='filter-type' label='Filter Type' type='text' value={filter_type()}
                   onChange={(event) => (set_filter_type(event.target.value))}/>
        <TextField id='window-type' label='Window Type' type='text'/>
        <TextField id='upload-file' label='File' type='file' InputLabelProps={{shrink: true}}/>
        <TextField id='upsampling_rate' label='Upsampling Ratio' type='number' value={upsampling_rate()}
                   onChange={(event) => (set_upsampling_rate(Number(event.target.value)))}/>
        <TextField id='low-cut' label='Low Cutoff' type='text' sx={{width: '150px'}}
                   inputProps={{inputMode: 'numeric', pattern: '[0-9]*\.[0-9]*'}}
                   onChange={(event) => set_low_cut(Number(event.target.value))}/>
        <TextField id='high-cut' label='High Cutoff' type='text' value={high_cut()} sx={{width: '150px'}}
                   onChange={(event) => set_high_cut(Number(event.target.value))}/>
        <Button variant='contained' id='process' onClick={fetch}><SearchIcon/></Button>
        <Switch id='show_spectrum' checked={show_spectrum()} onChange={() => set_show_spectrum(!show_spectrum())}/>
        <Switch id='show_response_spectrum' checked={show_response_spectrum()}
                onChange={() => set_show_response_spectrum(!show_response_spectrum())}/>
    </Stack>
}

const RecordCanvas: Component = () => {
    createEffect(() => {
        const original = {
            x: Array<number>(record().data.length).fill(0).map((_, i) => i * record().interval),
            y: record().data,
            type: 'scattergl', name: 'original'
        }
        const processed = {
            x: Array<number>(record().upsampled_waveform.length).fill(0).map((_, i) => i * record().upsampled_time_interval),
            y: record().upsampled_waveform,
            type: 'scattergl', name: 'processed'
        }

        Plotly.react(document.getElementById('process_canvas'), [original, processed], {
            autosize: true,
            automargin: true,
            title: {text: record().file_name, font: {size: 20},},
            xaxis: axis_label('Time (s)', 14),
            yaxis: axis_label('Amplitude (Gal)', 14),
            showlegend: true,
            legend: {
                x: 1,
                xanchor: 'right',
                y: 1
            }
        }, {responsive: true,})
    })

    return <Card id='process_canvas'></Card>
}

const SpectrumCanvas: Component = () => {
    createEffect(() => {
        const target = [
            {
                x: Array<number>(record().spectrum.length).fill(0).map((_, i) => i * record().frequency_interval),
                y: record().spectrum, type: 'scattergl', name: `original`
            },
            {
                x: Array<number>(record().upsampled_spectrum.length).fill(0).map((_, i) => i * record().upsampled_frequency_interval),
                y: record().upsampled_spectrum, type: 'scattergl', name: `processed`
            }
        ]

        Plotly.react(document.getElementById('spectrum_canvas'),
            target,
            {
                autosize: true,
                margin: {l: 60, r: 60, b: 60, t: 60, pad: 0},
                automargin: true,
                title: {text: `DFT`, font: {size: 14},},
                xaxis: Object.assign({}, axis_label('Frequency (Hz)', 12), {range: [0, record().spectrum.length * record().frequency_interval]}),
                yaxis: Object.assign({}, axis_label('Amplitude (Gal)', 12), {range: [0, Math.max(...record().spectrum) * 1.1]}),
                showlegend: false,
                legend: {
                    x: 1,
                    xanchor: 'right',
                    y: 1
                }
            }, {responsive: true,})
    })

    return <Card id='spectrum_canvas'></Card>
}

const ProcessPage: Component = () => {
    return <Grid container xs={12} spacing={2}>
        <Grid item xs={12}><ProcessConfig/></Grid>
        <Grid item xs={12}><RecordCanvas/></Grid>
        {(show_spectrum() || show_response_spectrum()) && <Grid container item xs={12} spacing={2}>
            {show_spectrum() && <Grid item xs={show_response_spectrum() ? 3 : 12}><SpectrumCanvas/></Grid>}
            {show_response_spectrum() &&
                <Grid item xs={show_spectrum() ? 3 : 4}>{ResponseSpectrum(record(), 'SA', 'sa_canvas')}</Grid>}
            {show_response_spectrum() &&
                <Grid item xs={show_spectrum() ? 3 : 4}>{ResponseSpectrum(record(), 'SV', 'sv_canvas')}</Grid>}
            {show_response_spectrum() &&
                <Grid item xs={show_spectrum() ? 3 : 4}>{ResponseSpectrum(record(), 'SD', 'sd_canvas')}</Grid>}
        </Grid>}
    </Grid>
}

export default ProcessPage