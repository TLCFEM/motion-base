import {Component, createEffect, For, onMount} from "solid-js"
import Grid from "@suid/material/Grid"
import Button from "@suid/material/Button"
// @ts-ignore
import L from 'leaflet'
import {DefaultMap, GreenIcon, Item, Record, RedIcon, StyledTableCell, StyledTableRow} from "./Utility"
import {createStore} from "solid-js/store"
import axios from "./API"
import tippy from "tippy.js"
import TableHead from "@suid/material/TableHead"
import TableRow from "@suid/material/TableRow"
import TableContainer from "@suid/material/TableContainer"
import Paper from "@suid/material/Paper"
import Table from "@suid/material/Table"
import TableBody from "@suid/material/TableBody"
// @ts-ignore
import * as ST from '@suid/types'

const [records, set_records] = createStore<Array<Record>>([]);

function RecordTableHeader(pool: Array<Record>) {
    const table_header: Array<string> = ['ID', 'Category', 'Mw', 'Event Time', 'Depth', 'Station', 'Sampling Freq.', 'Duration', 'Direction']

    const sort_by_magnitude = () =>
        set_records(pool.slice().sort((a, b) => b.magnitude - a.magnitude))

    const sort_by_time = () =>
        set_records(pool.slice().sort((a, b) => new Date(b.origin_time).getTime() - new Date(a.origin_time).getTime()))

    onMount(() => {
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

    return <StyledTableRow>
        <StyledTableCell component="th" scope="row">{record_entry.id}</StyledTableCell>
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

function RecordTable({pool}: { pool: Array<Record> }) {
    return <TableContainer component={Paper}>
        <Table sx={{minWidth: 1080}} size="small" aria-label="record-metadata">
            <RecordTableHeader {...pool}/>
            <TableBody>
                <For each={pool}>
                    {(record_entry) => <RecordEntry {...record_entry}/>}
                </For>
            </TableBody>
        </Table>
    </TableContainer>
}


const EventMap: Component = () => {
    let map: L.Map
    let marker_layer: L.LayerGroup

    onMount(() => {
        map = DefaultMap('event_map', [52.5068441, 13.4247317])
        marker_layer = L.layerGroup().addTo(map)
    })

    createEffect(() => {
        marker_layer.clearLayers()

        let x: number = 0
        let y: number = 0

        records.forEach((record: Record) => {
            const event_marker = L.marker(record.event_location.slice().reverse(), {icon: GreenIcon}).addTo(marker_layer)
            const station_marker = L.marker(record.station_location.slice().reverse(), {icon: RedIcon}).addTo(marker_layer)
            event_marker.bindPopup(record.id)
            station_marker.bindPopup(record.id)
            x += record.event_location[0] + record.station_location[0]
            y += record.event_location[1] + record.station_location[1]
        })

        if (records.length > 0) {
            x /= 2 * records.length
            y /= 2 * records.length
        } else {
            x = 13.4247317
            y = 52.5068441
        }

        map.flyTo([y, x], 6)
    })

    return <Item id='event_map'></Item>
}

async function fetch() {
    let region_value = 'nz'
    let url = `/${region_value}/query?page_size=40`
    await axios.post(url).then(
        res => {
            let obj = Array<Record>(res.data.result.length)
            for (let i = 0; i < res.data.result.length; i++) obj[i] = new Record(res.data.result[i])
            set_records(obj)
        }
    )
}

const SearchPage: Component = () => {
    return <Grid container spacing={1}>
        <Grid item xs={4}>
            <Button variant='contained' id='clear' onClick={fetch}>Search</Button>
        </Grid>
        <Grid container item xs={8} spacing={1}>
            <Grid item xs={12}><EventMap/></Grid>
            {records?.length > 0 && <Grid item xs={12}><RecordTable pool={records}/></Grid>}
        </Grid>
    </Grid>
}

export default SearchPage