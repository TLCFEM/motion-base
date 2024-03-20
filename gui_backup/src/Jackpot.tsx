import 'tippy.js/dist/tippy.css'
import 'tippy.js/themes/translucent.css'
import 'tippy.js/animations/scale.css'
import 'leaflet/dist/leaflet.css'
// @ts-ignore
import * as ST from '@suid/types'
import Alert from '@suid/material/Alert'
import axios from "./API"
import Button from '@suid/material/Button'
import CasinoIcon from '@suid/icons-material/Casino'
import CloudDownloadIcon from '@suid/icons-material/CloudDownload'
import DeleteOutlineIcon from '@suid/icons-material/DeleteOutline'
import FormControl from '@suid/material/FormControl'
import FormControlLabel from '@suid/material/FormControlLabel'
// @ts-ignore
import L from 'leaflet'
import LinearProgress from "@suid/material/LinearProgress"
import Modal from "@suid/material/Modal"
import Paper from "@suid/material/Paper"
// @ts-ignore
import Plotly from 'plotly.js-dist-min'
import Radio from '@suid/material/Radio'
import RadioGroup from '@suid/material/RadioGroup'
import Stack from "@suid/material/Stack"
import Switch from "@suid/material/Switch"
import Table from '@suid/material/Table'
import TableBody from '@suid/material/TableBody'
import TableContainer from '@suid/material/TableContainer'
import TableHead from '@suid/material/TableHead'
import TableRow from '@suid/material/TableRow'
import type {Component} from 'solid-js'
import {createEffect, createResource, createSignal, For, onMount} from 'solid-js'
import {createStore} from "solid-js/store"
import Grid from "@suid/material/Grid"
import tippy from "tippy.js"
import CircularProgress from "@suid/material/CircularProgress"
import {
    axis_label,
    DefaultMap,
    extract_response_spectrum,
    GreenIcon,
    Record,
    RedIcon,
    StyledTableCell,
    StyledTableRow
} from './Utility'
import {ResponseSpectrum} from "./ResponseSpectrum";
import Card from "@suid/material/Card";

const [open, set_open] = createSignal(false)
const [error_message, set_error_message] = createSignal('')

const modal_prop: object = {
    position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", border: "1px solid",
}

const ErrorModal = () => {
    return <Modal
        open={open()} onClose={() => set_open(false)} aria-labelledby="error-model" aria-describedby="error-model">
        <LinearProgress/>
        <Alert sx={modal_prop} severity="error">{error_message()}</Alert>
    </Modal>
}

const region_set: Array<string> = ['jp', 'nz']

const [normalised, set_normalised] = createSignal(false)
const [region, set_region] = createSignal(region_set[0])

const [waveform, set_waveform] = createSignal([Array<number>(0), Array<number>(0), ''])

const [record_pool, set_record_pool] = createStore<Array<Record>>(Array<Record>(0))
const [current_record, set_current_record] = createSignal<Record>(new Record({}))

function RecordTableHeader(pool: Array<Record>, set_pool: (pool: Array<Record>) => void) {
    const table_header: Array<string> = ['ID', 'File Name', 'Category', 'Mw', 'Event Time', 'Depth', 'PGA', 'Station', 'Sampling Freq.', 'Duration', 'Direction']

    const sort_by_magnitude = () =>
        set_pool(pool.slice().sort((a, b) => b.magnitude - a.magnitude))

    const sort_by_time = () =>
        set_pool(pool.slice().sort((a, b) => new Date(b.event_time).getTime() - new Date(a.event_time).getTime()))

    onMount(() => {
        tippy('#table-header-id', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'Click Target ID to Replot! ID Copied!',
        })

        tippy('#table-header-mw', {
            arrow: true, animation: 'scale', inertia: true, theme: 'translucent', content: 'Click Mw to Sort!',
        })

        tippy('#table-header-time', {
            arrow: true, animation: 'scale', inertia: true, theme: 'translucent', content: 'Click Event Time to Sort!',
        })
    })

    return <TableHead>
        <TableRow>
            <For each={table_header}>
                {(h) => {
                    if (h === 'ID') return <StyledTableCell id={'table-header-id'}>{h}</StyledTableCell>
                    if (h === 'Mw') return <StyledTableCell id={'table-header-mw'}
                                                            onClick={sort_by_magnitude}>{h}</StyledTableCell>
                    if (h === 'Event Time') return <StyledTableCell id={'table-header-time'}
                                                                    onClick={sort_by_time}>{h}</StyledTableCell>
                    return <StyledTableCell>{h}</StyledTableCell>
                }}
            </For>
        </TableRow>
    </TableHead>
}

function RecordEntry(record_entry: Record) {
    const convert_time = (time: string) => {
        if (time === '') return ''
        const date = new Date(time)
        return date.toLocaleString('en-GB')
    }

    const select_record = (event: ST.ChangeEvent<HTMLInputElement>) => {
        if (event.target.tagName != 'TH') return
        for (let i = 0; i < record_pool.length; i++)
            if (record_pool[i].id == event.target.innerText) {
                set_current_record(record_pool[i])
                navigator.clipboard.writeText(record_pool[i].id).then()
                break
            }
    }

    return <StyledTableRow>
        <StyledTableCell component="th" scope="row" onClick={select_record}>{record_entry.id}</StyledTableCell>
        <StyledTableCell>{record_entry.file_name}</StyledTableCell>
        <StyledTableCell>{record_entry.category}</StyledTableCell>
        <StyledTableCell>{record_entry.magnitude.toFixed(2)}</StyledTableCell>
        <StyledTableCell>{convert_time(record_entry.event_time)}</StyledTableCell>
        <StyledTableCell>{record_entry.depth} km</StyledTableCell>
        <StyledTableCell>{Math.abs(record_entry.maximum_acceleration).toFixed(1)}</StyledTableCell>
        <StyledTableCell>{record_entry.station_code}</StyledTableCell>
        <StyledTableCell>{record_entry.sampling_frequency} {record_entry.sampling_frequency_unit}</StyledTableCell>
        <StyledTableCell>{record_entry.duration.toFixed(0)} s</StyledTableCell>
        <StyledTableCell>{record_entry.direction}</StyledTableCell>
    </StyledTableRow>
}

function RecordTable(pool: Array<Record>, set_pool: (pool: Record[]) => void) {
    return <TableContainer component={Paper}>
        <Table sx={{minWidth: 1080}} size="small" aria-label="record-metadata">
            {RecordTableHeader(pool, set_pool)}
            <TableBody>
                <For each={pool}>
                    {(record_entry) => RecordEntry(record_entry)}
                </For>
            </TableBody>
        </Table>
    </TableContainer>
}

function clear() {
    set_record_pool(Array<Record>(0))
    set_current_record(new Record({}))
}

async function jackpot() {
    let region_value = region()
    if (region_value === 'us' || region_value === 'eu') region_value = 'jp'
    let url = '/waveform/jackpot'
    if (normalised()) url += '?normalised=true'
    let new_record: Record
    await axios.get(url).then(async res => {
        new_record = new Record(res.data)
        url = `/${region_value}/response_spectrum/${new_record.id}`
        if (normalised()) url += '?normalised=true'
        await axios.get(url).then(res => {
            new_record.period = res.data.period
            new_record.displacement_spectrum = res.data.displacement_spectrum
            new_record.velocity_spectrum = res.data.velocity_spectrum
            new_record.acceleration_spectrum = res.data.acceleration_spectrum
            set_current_record(new_record)
            set_record_pool([...record_pool, new_record])
        }).catch(err => {
            set_error_message('Fail to retrieve data: ' + err.message)
            set_open(true)
        })
    }).catch(err => {
        set_error_message('Fail to retrieve data: ' + err.message)
        set_open(true)
    })
}

const [data, {mutate, refetch}] = createResource(jackpot);

const Epicenter: Component = () => {
    let map: L.Map
    let event_marker: L.Marker
    let station_marker: L.Marker

    onMount(() => {
        const event_location = current_record().event_location.slice().reverse()
        map = DefaultMap('epicenter', event_location)

        event_marker = L.marker(event_location, {icon: RedIcon}).addTo(map)
        station_marker = L.marker(current_record().station_location.slice().reverse(), {icon: GreenIcon}).addTo(map)

        event_marker.bindPopup('event location')
        station_marker.bindPopup('station location')
    })

    createEffect(() => {
        const metadata = current_record()

        const event_location = metadata.event_location.slice().reverse()
        map.flyTo(event_location, 6)

        event_marker.setLatLng(event_location)
        station_marker.setLatLng(metadata.station_location.slice().reverse())

        const interval: number = metadata.interval

        const x: Array<number> = Array<number>(metadata.data.length).fill(0).map((_, i) => i * interval)

        set_waveform([x, metadata.data, metadata.file_name])
    })

    return <Card id='epicenter'></Card>
}

const Waveform: Component = () => {
    createEffect(() => {
        const trace = {x: waveform()[0], y: waveform()[1], type: 'scatter', name: waveform()[2]}

        Plotly.react(document.getElementById('canvas'), [trace], {
            autosize: true,
            automargin: true,
            title: {text: waveform()[2], font: {size: 20},},
            xaxis: axis_label('Time (s)', 14),
            yaxis: axis_label('Amplitude (Gal)', 14),
        }, {responsive: true,})
    })

    return <Card id='canvas'></Card>
}

function download() {
    const record = current_record()

    if (record.period.length === 0) {
        set_error_message('No data to download.')
        set_open(true)
        return
    }

    const data = new Blob([JSON.stringify({
        'time': waveform()[0],
        'waveform': record.data,
        'period': record.period,
        'displacement_spectrum': record.displacement_spectrum,
        'velocity_spectrum': record.velocity_spectrum,
        'acceleration_spectrum': record.acceleration_spectrum
    })], {type: 'application/json'})

    const url = window.URL.createObjectURL(data)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', record.file_name + '.json')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
}

function RegionGroup() {
    onMount(() => {
        tippy('#random', {
            arrow: true, animation: 'scale', inertia: true, theme: 'translucent', content: 'Get a Random Waveform!',
        })

        tippy('#normalised', {
            arrow: true, animation: 'scale', inertia: true, theme: 'translucent', content: 'if normalised',
        })

        tippy('#clear', {
            arrow: true, animation: 'scale', inertia: true, theme: 'translucent', content: 'Clear the Table!',
        })

        tippy('#download', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'Download Current Record as json!',
        })
    })

    return <Stack component={Card} spacing={1} justifyContent='center' direction='column' alignItems='center'
                  alignContent='center'>
        <FormControl size='small'>
            <RadioGroup aria-labelledby='region' name='region' id='region' value={region()}
                        onChange={event => set_region(event.target.value)}>
                <For each={region_set}>
                    {(r) => <FormControlLabel value={r} control={<Radio size='small'/>} label={r.toUpperCase()}/>}
                </For>
            </RadioGroup>
        </FormControl>
        <Switch id='normalised' checked={normalised()} onChange={() => set_normalised(!normalised())}/>
        <Button variant='contained' id='random' onClick={refetch} disabled={data?.loading}>
            {data?.loading ? <CircularProgress color="secondary" size={24}/> : <CasinoIcon/>}
        </Button>
        <Button variant='contained' id='clear' onClick={clear}><DeleteOutlineIcon/></Button>
        <Button variant='contained' id='download' onClick={download}><CloudDownloadIcon/></Button>
    </Stack>
}

const Jackpot: Component = () => {
    return <>
        <Grid container spacing={1}>
            <Grid item xs={1}>
                <RegionGroup/>
            </Grid>
            <Grid container item xs={11} spacing={1}>
                <Grid item xs={8}><Waveform/></Grid>
                <Grid item xs={4}><Epicenter/></Grid>
                <Grid item xs={4}>{ResponseSpectrum([
                    extract_response_spectrum(current_record(), 'original', 'SA')
                ], 'SA', 'spectrum_sa')}</Grid>
                <Grid item xs={4}>{ResponseSpectrum([
                    extract_response_spectrum(current_record(), 'original', 'SV')
                ], 'SV', 'spectrum_sv')}</Grid>
                <Grid item xs={4}>{ResponseSpectrum([
                    extract_response_spectrum(current_record(), 'original', 'SD')
                ], 'SD', 'spectrum_sd')}</Grid>
                {record_pool?.length > 0 && <Grid item xs={12}>{RecordTable(record_pool, set_record_pool)}</Grid>}
            </Grid>
        </Grid>
        <ErrorModal/>
    </>
}

export default Jackpot