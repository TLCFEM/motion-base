import {Component, createEffect, createSignal} from "solid-js"
import {axis_label, Item, Record} from "./Utility"
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

const [raw_waveform, set_raw_waveform] = createSignal([Array<number>(0), Array<number>(0), ''])
const [processed_waveform, set_processed_waveform] = createSignal([Array<number>(0), Array<number>(0), ''])
const [record_id, set_record_id] = createSignal('')
const [upsampling_rate, set_upsampling_rate] = createSignal(2)
const [filter_length, set_filter_length] = createSignal(0)
const [filter_type, set_filter_type] = createSignal('bandpass')
const [region, set_region] = createSignal('jp')

async function fetch() {
    let url = `/${region()}/waveform/${record_id()}`
    await axios.get(url).then(
        res => {
            const record = new Record(res.data)
            const x: Array<number> = Array<number>(record.data.length).fill(0).map((_, i) => i * record.interval)
            set_raw_waveform([x, record.data, record.file_name])
        }
    )

    url = `/${region()}/process?record_id=${record_id()}&upsampling_rate=${upsampling_rate()}`
    await axios.post(url).then(
        res => {
            const record = new Record(res.data)
            const x: Array<number> = Array<number>(record.data.length).fill(0).map((_, i) => i * record.interval)
            set_processed_waveform([x, record.data, record.file_name])
        }
    )
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
    </Stack>
}

const RecordCanvas: Component = () => {
    createEffect(() => {
        const original = {x: raw_waveform()[0], y: raw_waveform()[1], type: 'scattergl', name: 'original'}
        const processed = {x: processed_waveform()[0], y: processed_waveform()[1], type: 'scattergl', name: 'processed'}

        Plotly.react(document.getElementById('process_canvas'), [original, processed], {
            autosize: true,
            automargin: true,
            title: {text: raw_waveform()[2], font: {size: 20},},
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

const ProcessPage: Component = () => {
    return <Grid container xs={12} spacing={2}>
        <Grid item xs={12}>
            <ProcessConfig/></Grid>
        <Grid item xs={12}>
            <RecordCanvas/></Grid>
    </Grid>
}

export default ProcessPage