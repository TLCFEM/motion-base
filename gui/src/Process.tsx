import {Component, createEffect, createSignal} from "solid-js"
import {axis_label, Item, Record, ResponseSpectrum} from "./Utility"
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

const [record, set_record] = createSignal<Record>(new Record({}))

const [record_id, set_record_id] = createSignal('')
const [upsampling_rate, set_upsampling_rate] = createSignal(2)
const [filter_length, set_filter_length] = createSignal(8)
const [filter_type, set_filter_type] = createSignal('bandpass')
const [region, set_region] = createSignal('jp')

const [show_spectrum, set_show_spectrum] = createSignal(false)
const [show_response_spectrum, set_show_response_spectrum] = createSignal(false)

async function fetch() {
    let url = `/${region()}/waveform/${record_id()}`
    let new_record: Record = new Record({})
    await axios.get(url).then(
        res => new_record = new Record(res.data)
    )

    url = `/${region()}/process?record_id=${record_id()}&upsampling_rate=${upsampling_rate()}&filter_length=${filter_length()}`
    await axios.post(url).then(
        res => {
            new_record.upsampled_interval = res.data.interval
            new_record.upsampled_data = res.data.data
        }
    )

    if (show_spectrum()) {
        url = `/${region()}/spectrum/${record_id()}`
        await axios.get(url).then(
            res => {
                new_record.frequency = res.data.interval
                new_record.spectrum = res.data.data
            }
        )
    }

    if (show_response_spectrum()) {
        url = `/${region()}/response_spectrum/${record_id()}`
        await axios.get(url).then(
            res => {
                new_record.period = res.data.data.map((d: Array<number>) => d[0])
                new_record.SD = res.data.data.map((d: Array<number>) => d[1])
                new_record.SV = res.data.data.map((d: Array<number>) => d[2])
                new_record.SA = res.data.data.map((d: Array<number>) => d[3])
            }
        )
    }

    set_record(new_record)
}

function ProcessConfig() {
    return <Stack component='form' noValidate alignContent='center' justifyContent='center' alignItems='center'
                  direction='row' spacing={2} autocomplete='off'>
        <TextField id='record-id' label='Record ID' type='text'
                   onChange={(event: ST.ChangeEvent<HTMLInputElement>) => {
                       set_record_id(event.target.value)
                   }}/>
        <TextField id='upsampling_rate' label='Upsampling Ratio' type='number'
                   onChange={(event: ST.ChangeEvent<HTMLInputElement>) => {
                       set_upsampling_rate(event.target.value)
                   }}/>
        <TextField id='filter_length' label='Filter Length' type='number'
                   onChange={(event: ST.ChangeEvent<HTMLInputElement>) => {
                       set_filter_length(event.target.value)
                   }}/>
        <TextField id='filter-type' label='Filter Type' type='text'
                   onChange={(event: ST.ChangeEvent<HTMLInputElement>) => {
                       set_filter_type(event.target.value)
                   }}/>
        <TextField id='window-type' label='Window Type' type='text'/>
        <TextField id='low-cut' label='Low Cutoff' type='number'/>
        <TextField id='high-cut' label='High Cutoff' type='number'/>
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
            x: Array<number>(record().upsampled_data.length).fill(0).map((_, i) => i * record().upsampled_interval),
            y: record().upsampled_data,
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

    return <Item id='process_canvas'></Item>
}

const SpectrumCanvas: Component = () => {
    createEffect(() => {
        Plotly.react(document.getElementById('spectrum_canvas'),
            [{
                x: Array<number>(record().spectrum.length).fill(0).map((_, i) => i * record().frequency),
                y: record().spectrum, type: 'scatter', name: `DFT`
            }],
            {
                autosize: true,
                margin: {l: 60, r: 60, b: 60, t: 60, pad: 0},
                automargin: true,
                title: {text: `DFT`, font: {size: 14},},
                xaxis: Object.assign({}, axis_label('Frequency (Hz)', 12), {range: [0, record().spectrum.length * record().frequency]}),
                yaxis: Object.assign({}, axis_label('Amplitude (Gal)', 12), {range: [0, Math.max(...record().spectrum) * 1.1]}),
                showlegend: false,
                legend: {
                    x: 1,
                    xanchor: 'right',
                    y: 1
                }
            }, {responsive: true,})
    })

    return <Item id='spectrum_canvas'></Item>
}

const ProcessPage: Component = () => {
    return <Grid container xs={12} spacing={2}>
        <Grid item xs={12}><ProcessConfig/></Grid>
        <Grid item xs={12}><RecordCanvas/></Grid>
        {(show_spectrum() || show_response_spectrum()) && <Grid container item xs={12} spacing={2}>
            {show_spectrum() && <Grid item xs={3}><SpectrumCanvas/></Grid>}
            {show_response_spectrum() && <Grid item xs={3}>{ResponseSpectrum(record(), 'SA', 'sa_canvas')}</Grid>}
            {show_response_spectrum() && <Grid item xs={3}>{ResponseSpectrum(record(), 'SV', 'sv_canvas')}</Grid>}
            {show_response_spectrum() && <Grid item xs={3}>{ResponseSpectrum(record(), 'SD', 'sd_canvas')}</Grid>}
        </Grid>}
    </Grid>
}

export default ProcessPage