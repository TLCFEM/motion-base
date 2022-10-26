import 'tippy.js/dist/tippy.css'
import 'tippy.js/themes/translucent.css'
import 'tippy.js/animations/scale.css'
import 'leaflet/dist/leaflet.css'
// @ts-ignore
import * as ST from '@suid/types'
import Alert from '@suid/material/Alert'
import axios from "axios"
import Button from '@suid/material/Button'
import CasinoIcon from '@suid/icons-material/Casino'
import DeleteOutlineIcon from '@suid/icons-material/DeleteOutline'
import FormControl from '@suid/material/FormControl'
import FormControlLabel from '@suid/material/FormControlLabel'
// @ts-ignore
import L from 'leaflet'
import LinearProgress from "@suid/material/LinearProgress";
import Modal from "@suid/material/Modal";
import Paper from "@suid/material/Paper"
// @ts-ignore
import Plotly from 'plotly.js-dist-min'
import Radio from '@suid/material/Radio'
import RadioGroup from '@suid/material/RadioGroup'
import Stack from "@suid/material/Stack"
import styled from "@suid/material/styles/styled"
import Switch from "@suid/material/Switch";
import Table from '@suid/material/Table'
import TableBody from '@suid/material/TableBody'
import TableCell, {tableCellClasses} from '@suid/material/TableCell'
import TableContainer from '@suid/material/TableContainer'
import TableHead from '@suid/material/TableHead'
import TableRow from '@suid/material/TableRow'
import type {Component} from 'solid-js'
import {createEffect, createSignal, For, onMount} from 'solid-js'
import {createStore} from "solid-js/store";
import Grid from "@suid/material/Grid";
import tippy from "tippy.js";

const [open, set_open] = createSignal(false);
const [error_message, set_error_message] = createSignal('');

const ErrorModal = () => {
    const error_toggle_off = () => set_open(false);

    return <Modal
        open={open()} onClose={error_toggle_off} aria-labelledby="error-model"
        aria-describedby="error-model">
        <LinearProgress/>
        <Alert sx={{
            position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", border: "1px solid",
        }} severity="error">{error_message()}</Alert>
    </Modal>
}

const region_set: Array<string> = ['jp', 'nz']

const [normalised, set_normalised] = createSignal(false);
const [region, set_region] = createSignal(region_set[0])

function RegionGroup() {
    const handle_change = (event: ST.ChangeEvent<HTMLInputElement>) => set_region(event.target.value)
    const handle_normalised = () => set_normalised(!normalised())

    return <Stack component={Item} justifyContent='center' direction='column' alignItems='center' alignContent='center'>
        <FormControl size='small'>
            <RadioGroup aria-labelledby='region' name='region' id='region' row={true} value={region()}
                        onChange={handle_change}>
                <For each={region_set}>
                    {(r) => <FormControlLabel value={r} control={<Radio size='small'/>} label={r.toUpperCase()}/>}
                </For>
            </RadioGroup>
        </FormControl>
        <Switch id='normalised' checked={normalised()} onChange={handle_normalised}/>
        <Button variant='contained' id='random' onClick={jackpot}><CasinoIcon/></Button>
        <Button variant='contained' id='clear' onClick={clear}><DeleteOutlineIcon/></Button>
    </Stack>
}

const [event_location, set_event_location] = createSignal([52.5068441, 13.4247317])
const [station_location, set_station_location] = createSignal([52.5068441, 13.4247317])
const [waveform, set_waveform] = createSignal([Array<number>(0), Array<number>(0), ''])

class Record {
    public id: string = ''
    public file_name: string = ''
    public sub_category: string = ''
    public magnitude: number = 0
    public origin_time: string = ''
    public latitude: number = 52.5068441
    public longitude: number = 13.4247317
    public depth: number = 0
    public depth_unit: string = ''
    public station_code: string = ''
    public station_latitude: number = 52.5068441
    public station_longitude: number = 13.4247317
    public sampling_frequency: number = 0
    public sampling_frequency_unit: string = ''
    public duration: number = 0
    public duration_unit: string = ''
    public direction: string = ''

    public interval: number = 0
    public data: Array<number> = Array<number>(0)

    // response spectrum related
    public freq: Array<number> = Array<number>(0)
    public SA: Array<number> = Array<number>(0)
    public SV: Array<number> = Array<number>(0)
    public SD: Array<number> = Array<number>(0)

    public constructor(data: any) {
        Object.assign(this, data)
    }
}

const [record_metadata, set_record_metadata] = createStore<Array<Record>>(Array<Record>(0))
const [current_record, set_current_record] = createSignal<Record>(new Record({}))

const StyledTableCell = styled(TableCell)(({theme}) => ({
    [`&.${tableCellClasses.head}`]: {
        backgroundColor: theme.palette.primary.main, // backgroundColor: theme.palette.common.black,
        color: theme.palette.common.white,
    }, [`&.${tableCellClasses.body}`]: {
        fontSize: 14,
    },
}))

const StyledTableRow = styled(TableRow)(({theme}) => ({
    '&:nth-of-type(odd)': {
        backgroundColor: theme.palette.action.hover,
    }, '&:last-child td, &:last-child th': {
        border: 0,
    },
}))

const sort_by_magnitude = (event: ST.ChangeEvent<HTMLInputElement>) => {
    set_record_metadata(record_metadata.slice().sort((a, b) => b.magnitude - a.magnitude))
}

const sort_by_time = (event: ST.ChangeEvent<HTMLInputElement>) =>
    set_record_metadata(record_metadata.slice().sort((a, b) => new Date(b.origin_time).getTime() - new Date(a.origin_time).getTime()))

function RecordTableHeader() {
    const table_header: Array<string> = ['ID', 'File Name', 'Category', 'Mw', 'Event Time', 'Depth', 'Station', 'Sampling Freq.', 'Duration', 'Direction']

    onMount(() => {
        tippy('#table-header-id', {
            arrow: true, animation: 'scale', inertia: true, theme: 'translucent', content: 'Click Target ID to Replot!',
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

const select_record = (event: ST.ChangeEvent<HTMLInputElement>) => {
    if (event.target.tagName != 'TH') return
    for (let i = 0; i < record_metadata.length; i++)
        if (record_metadata[i].id == event.target.innerText) {
            set_current_record(record_metadata[i])
            break
        }
}

function RecordEntry(record_entry: Record) {
    const convert_time = (time: string) => {
        if (time === '') return ''
        const date = new Date(time)
        return date.toLocaleString('en-GB')
    }

    return <StyledTableRow>
        <StyledTableCell component="th" scope="row" onClick={select_record}>{record_entry.id}</StyledTableCell>
        <StyledTableCell>{record_entry.file_name}</StyledTableCell>
        <StyledTableCell>{record_entry.sub_category}</StyledTableCell>
        <StyledTableCell>{record_entry.magnitude.toFixed(2)}</StyledTableCell>
        <StyledTableCell>{convert_time(record_entry.origin_time)}</StyledTableCell>
        <StyledTableCell>{record_entry.depth} {record_entry.depth_unit}</StyledTableCell>
        <StyledTableCell>{record_entry.station_code}</StyledTableCell>
        <StyledTableCell>{record_entry.sampling_frequency} {record_entry.sampling_frequency_unit}</StyledTableCell>
        <StyledTableCell>{record_entry.duration.toFixed(0)} {record_entry.duration_unit}</StyledTableCell>
        <StyledTableCell>{record_entry.direction}</StyledTableCell>
    </StyledTableRow>
}

function RecordTable() {
    return <TableContainer component={Paper}>
        <Table sx={{minWidth: 1080}} size="small" aria-label="record-metadata">
            <RecordTableHeader/>
            <TableBody>
                <For each={record_metadata}>
                    {(record_entry) => <RecordEntry {...record_entry}/>}
                </For>
            </TableBody>
        </Table>
    </TableContainer>
}

const axis_label = (label: string, size: number) => {
    return {
        title: {
            text: label, font: {
                size: size, color: '#1f78b4'
            }
        },
    }
}

function clear() {
    set_record_metadata(Array<Record>(0))
}

async function jackpot() {
    let region_value = region()
    if (region_value === 'us' || region_value === 'eu') region_value = 'jp'
    let url = `/${region_value}/waveform/jackpot`
    if (normalised()) url += '?normalised=true'
    let new_record: Record
    await axios.get(url).then(async res => {
        if (res.status !== 200) return
        new_record = new Record(res.data)
        url = `/${region_value}/response_spectrum/${new_record.id}`
        await axios.get(url).then(res => {
            if (res.status !== 200) return
            new_record.freq = res.data.data.map((d: Array<number>) => d[0])
            new_record.SD = res.data.data.map((d: Array<number>) => d[1])
            new_record.SV = res.data.data.map((d: Array<number>) => d[2])
            new_record.SA = res.data.data.map((d: Array<number>) => d[3])
            set_current_record(new_record)
            set_record_metadata([...record_metadata, new_record])
        }).catch(err => {
            set_error_message('Fail to retrieve data: ' + err.message)
            set_open(true)
        })
    }).catch(err => {
        set_error_message('Fail to retrieve data: ' + err.message)
        set_open(true)
    })
}

const Item = styled(Paper)(({theme}) => ({
    backgroundColor: theme.palette.mode === 'dark' ? '#1A2027' : '#fff',
    ...theme.typography.body2,
    padding: theme.spacing(1),
    textAlign: 'center',
    color: theme.palette.text.secondary,
}));

const Epicenter: Component = () => {
    let map: L.Map
    let event_marker: L.Marker
    let station_marker: L.Marker
    const LeafIcon = L.Icon.extend({
        options: {
            iconSize: [38, 95],
            shadowSize: [50, 64],
            iconAnchor: [22, 94],
            shadowAnchor: [4, 62],
            popupAnchor: [-3, -76]
        }
    });
    const event_icon = new LeafIcon({
        iconUrl: 'http://leafletjs.com/examples/custom-icons/leaf-red.png',
        shadowUrl: 'http://leafletjs.com/examples/custom-icons/leaf-shadow.png'
    })
    const station_icon = new LeafIcon({
        iconUrl: 'http://leafletjs.com/examples/custom-icons/leaf-green.png',
        shadowUrl: 'http://leafletjs.com/examples/custom-icons/leaf-shadow.png'
    })

    onMount(() => {
        map = L.map(document.getElementById('epicenter')).setView(event_location(), 6)

        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 12, attribution: '© OpenStreetMap'
        }).addTo(map)

        event_marker = L.marker(event_location(), {icon: event_icon}).addTo(map)
        station_marker = L.marker(station_location(), {icon: station_icon}).addTo(map)

        event_marker.bindPopup('event location')
        station_marker.bindPopup('station location')

        tippy('#random', {
            arrow: true, animation: 'scale', inertia: true, theme: 'translucent', content: 'Get a Random Waveform!',
        })

        tippy('#normalised', {
            arrow: true, animation: 'scale', inertia: true, theme: 'translucent', content: 'if normalised',
        })

        tippy('#clear', {
            arrow: true, animation: 'scale', inertia: true, theme: 'translucent', content: 'Clear the Table!',
        })

        jackpot().then()
    })

    createEffect(() => {
        event_marker.setLatLng(event_location())
        station_marker.setLatLng(station_location())

        map.flyTo(event_location(), 6)
    })

    createEffect(() => {
        const metadata = current_record()

        set_event_location([metadata.latitude, metadata.longitude])
        set_station_location([metadata.station_latitude, metadata.station_longitude])

        const interval: number = metadata.interval

        let x: Array<number> = []
        for (let i = 0; i < metadata.data.length; i++) x.push(i * interval)

        set_waveform([x, metadata.data, metadata.file_name])
    })

    return <Item id='epicenter'></Item>
}

const Waveform: Component = () => {
    createEffect(() => {
        const trace = {x: waveform()[0], y: waveform()[1], type: 'scatter', name: waveform()[2]}

        Plotly.newPlot(document.getElementById('canvas'), [trace], {
            autosize: true,
            automargin: true,
            title: {text: waveform()[2], font: {size: 20},},
            xaxis: axis_label('Time (s)', 14),
            yaxis: axis_label('Amplitude (Gal)', 14),
        }, {responsive: true,})
    })

    return <Item id='canvas'></Item>
}

const SpectrumSA: Component = () => {
    createEffect(() => {
        Plotly.newPlot(document.getElementById('spectrum_sa'),
            [{x: current_record().freq, y: current_record().SA, type: 'scatter', name: 'SA (5% damping)'}],
            {
                autosize: true,
                margin: {l: 40, r: 40, b: 40, t: 40, pad: 0},
                automargin: true,
                title: {text: 'SA (5% damping)', font: {size: 14},},
                xaxis: Object.assign({}, axis_label('Period (s)', 12), {range: [0, current_record().freq[current_record().freq.length - 1]]}),
                yaxis: Object.assign({}, axis_label('Amplitude (Gal)', 12), {range: [0, Math.max(...current_record().SA) * 1.1]}),
                showlegend: false,
                legend: {
                    x: 1,
                    xanchor: 'right',
                    y: 1
                }
            }, {responsive: true,})
    })

    return <Item id='spectrum_sa'></Item>
}

const SpectrumSV: Component = () => {
    createEffect(() => {
        Plotly.newPlot(document.getElementById('spectrum_sv'),
            [{x: current_record().freq, y: current_record().SV, type: 'scatter', name: 'SV (5% damping)'}],
            {
                autosize: true,
                margin: {l: 40, r: 40, b: 40, t: 40, pad: 0},
                automargin: true,
                title: {text: 'SV (5% damping)', font: {size: 14},},
                xaxis: Object.assign({}, axis_label('Period (s)', 12), {range: [0, current_record().freq[current_record().freq.length - 1]]}),
                yaxis: Object.assign({}, axis_label('Amplitude (cm/s)', 12), {range: [0, Math.max(...current_record().SV) * 1.1]}),
                showlegend: false,
                legend: {
                    x: 1,
                    xanchor: 'right',
                    y: 1
                }
            }, {responsive: true,})
    })

    return <Item id='spectrum_sv'></Item>
}

const SpectrumSD: Component = () => {
    createEffect(() => {
        Plotly.newPlot(document.getElementById('spectrum_sd'),
            [{x: current_record().freq, y: current_record().SD, type: 'scatter', name: 'SD (5% damping)'}],
            {
                autosize: true,
                margin: {l: 40, r: 40, b: 40, t: 40, pad: 0},
                automargin: true,
                title: {text: 'SD (5% damping)', font: {size: 14},},
                xaxis: Object.assign({}, axis_label('Period (s)', 12), {range: [0, current_record().freq[current_record().freq.length - 1]]}),
                yaxis: Object.assign({}, axis_label('Amplitude (cm)', 12), {range: [0, Math.max(...current_record().SD) * 1.1]}),
                showlegend: false,
                legend: {
                    x: 1,
                    xanchor: 'right',
                    y: 1
                }
            }, {responsive: true,})
    })

    return <Item id='spectrum_sd'></Item>
}

const Jackpot: Component = () => {
    return <>
        <Grid container spacing={1}>
            <Grid item xs={2}>
                <RegionGroup/>
            </Grid>
            <Grid container item xs={10} spacing={1}>
                <Grid item xs={8}><Waveform/></Grid>
                <Grid item xs={4}><Epicenter/></Grid>
                <Grid item xs={4}><SpectrumSA/></Grid>
                <Grid item xs={4}><SpectrumSV/></Grid>
                <Grid item xs={4}><SpectrumSD/></Grid>
                <Grid item xs={12}><RecordTable/></Grid>
            </Grid>
        </Grid>
        <ErrorModal/>
    </>
}

export default Jackpot
