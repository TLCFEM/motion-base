import {Component, createEffect, createSignal, For, onMount} from 'solid-js'
import Grid from '@suid/material/Grid'
import Button from '@suid/material/Button'
// @ts-ignore
import L from 'leaflet'
import {DefaultMap, GreenIcon, Item, Record, RedIcon, StyledTableCell, StyledTableRow} from './Utility'
import {createStore} from 'solid-js/store'
import axios from './API'
import tippy from 'tippy.js'
import TableHead from '@suid/material/TableHead'
import TableRow from '@suid/material/TableRow'
import TableContainer from '@suid/material/TableContainer'
import Paper from '@suid/material/Paper'
import Table from '@suid/material/Table'
import TableBody from '@suid/material/TableBody'
import Box from '@suid/material/Box'
import TextField from '@suid/material/TextField'
// @ts-ignore
import * as ST from '@suid/types'
import ToggleButton from '@suid/material/ToggleButton'
import ToggleButtonGroup from '@suid/material/ToggleButtonGroup'
import SearchIcon from '@suid/icons-material/Search'

const [records, set_records] = createStore<Array<Record>>([]);

function RecordTableHeader(pool: Array<Record>) {
    const table_header: Array<string> = ['ID', 'Category', 'Mw', 'Event Time', 'Depth', 'PGA', 'Station', 'Sampling Freq.', 'Duration', 'Direction']

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
        <StyledTableCell component='th' scope='row'>{record_entry.id}</StyledTableCell>
        <StyledTableCell>{record_entry.sub_category}</StyledTableCell>
        <StyledTableCell>{record_entry.magnitude.toFixed(2)}</StyledTableCell>
        <StyledTableCell>{convert_time(record_entry.origin_time)}</StyledTableCell>
        <StyledTableCell>{record_entry.depth} km</StyledTableCell>
        <StyledTableCell>{Math.abs(record_entry.maximum_acceleration).toFixed(1)}</StyledTableCell>
        <StyledTableCell>{record_entry.station_code}</StyledTableCell>
        <StyledTableCell>{record_entry.sampling_frequency} {record_entry.sampling_frequency_unit}</StyledTableCell>
        <StyledTableCell>{record_entry.duration.toFixed(0)} s</StyledTableCell>
        <StyledTableCell>{record_entry.direction}</StyledTableCell>
    </StyledTableRow>
}

function RecordTable({pool}: { pool: Array<Record> }) {
    return <TableContainer component={Paper}>
        <Table sx={{minWidth: 1080}} size='small' aria-label='record-metadata'>
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

const [alignment, set_alignment] = createSignal('jp')
const [page_size, set_page_size] = createSignal(20)
const [min_mag, set_min_mag] = createSignal(0)
const [max_mag, set_max_mag] = createSignal(10)
const [min_pga, set_min_pga] = createSignal(0)
const [max_pga, set_max_pga] = createSignal(0)

async function fetch() {
    let url = `/${alignment()}/query?page_size=${page_size() > 0 ? page_size() : 20}`
    if (min_mag() > 0) url += `&min_magnitude=${min_mag()}`
    if (max_mag() > 0 && max_mag() >= min_mag()) url += `&max_magnitude=${max_mag()}`
    if (min_pga() > 0) url += `&min_pga=${min_pga()}`
    if (max_pga() > 0 && max_pga() >= min_pga()) url += `&max_pga=${max_pga()}`
    console.log(page_size())
    await axios.post(url).then(
        res => {
            let obj = Array<Record>(res.data.result.length)
            for (let i = 0; i < res.data.result.length; i++) obj[i] = new Record(res.data.result[i])
            set_records(obj)
        }
    )
}

function ColorToggleButton() {
    return (
        <ToggleButtonGroup color='primary' value={alignment()} exclusive onChange={(event, new_alignment) => {
            set_alignment(new_alignment);
        }}>
            <ToggleButton value='jp'>Japan</ToggleButton>
            <ToggleButton value='nz'>New Zealand</ToggleButton>
        </ToggleButtonGroup>
    );
}

function SearchConfig() {
    return (
        <Box component='form' sx={{[`& .${TextField}`]: {m: 1, width: '15ch'}, textAlign: 'center',}} noValidate
             autocomplete='off'>
            <div>
                <ColorToggleButton/>
                <Button variant='contained' id='clear' onClick={fetch}><SearchIcon/></Button>
            </div>
            <div>
                <TextField id='min-magnitude' label='Min. Mag.' type='number'
                           onChange={(event: ST.ChangeEvent<HTMLInputElement>) => {
                               set_min_mag(event.target.value)
                           }}/>
                <TextField id='max-magnitude' label='Max. Mag.' type='number'
                           onChange={(event: ST.ChangeEvent<HTMLInputElement>) => {
                               set_max_mag(event.target.value)
                           }}/>
            </div>
            <div>
                <TextField id='min-pga' label='Min. PGA' type='number'
                           onChange={(event: ST.ChangeEvent<HTMLInputElement>) => {
                               set_min_pga(event.target.value)
                           }}/>
                <TextField id='max-pga' label='Max. PGA' type='number'
                           onChange={(event: ST.ChangeEvent<HTMLInputElement>) => {
                               set_max_pga(event.target.value)
                           }}/>
            </div>
            <div>
                <TextField id='event_lat' label='Event Lat.' type='number'/>
                <TextField id='event_log' label='Event Log.' type='number'/>
            </div>
            <div>
                <TextField id='station_lat' label='Station Lat.' type='number'/>
                <TextField id='station_log' label='Station Log.' type='number'/>
            </div>
            <div>
                <TextField id='page_size' label='Records per Page' type='number' defaultValue={20}
                           onChange={(event: ST.ChangeEvent<HTMLInputElement>) => {
                               set_page_size(event.target.value)
                           }}/>
            </div>
        </Box>
    );
}

const SearchPage: Component = () => {
    return <Grid container spacing={1}>
        <Grid item xs={3}>
            <SearchConfig/>
        </Grid>
        <Grid container item xs={9} spacing={1}>
            <Grid item xs={12}><EventMap/></Grid>
            {records?.length > 0 && <Grid item xs={12}><RecordTable pool={records}/></Grid>}
        </Grid>
    </Grid>
}

export default SearchPage