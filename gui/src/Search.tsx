import {Component, createEffect, createSignal, For, onMount} from 'solid-js'
import Grid from '@suid/material/Grid'
import Button from '@suid/material/Button'
// @ts-ignore
import L from 'leaflet'
import {DefaultMap, GreenIcon, Record, RedIcon, StyledTableCell, StyledTableRow} from './Utility'
import {createStore} from 'solid-js/store'
import axios from './API'
import tippy from 'tippy.js'
import TableHead from '@suid/material/TableHead'
import TableRow from '@suid/material/TableRow'
import TableContainer from '@suid/material/TableContainer'
import Paper from '@suid/material/Paper'
import Table from '@suid/material/Table'
import TableBody from '@suid/material/TableBody'
import TextField from '@suid/material/TextField'
// @ts-ignore
import * as ST from '@suid/types'
import ToggleButton from '@suid/material/ToggleButton'
import ToggleButtonGroup from '@suid/material/ToggleButtonGroup'
import SearchIcon from '@suid/icons-material/Search'
import Stack from "@suid/material/Stack";
import Card from "@suid/material/Card";
import Switch from "@suid/material/Switch";

const [records, set_records] = createStore<Array<Record>>([]);

function RecordTableHeader(pool: Array<Record>) {
    const table_header: Array<string> = ['ID', 'File Name', 'Category', 'Mw', 'Event Time', 'Depth', 'PGA', 'Station', 'Sampling Freq.', 'Duration', 'Direction']

    const sort_by_magnitude = () =>
        set_records(pool.slice().sort((a, b) => b.magnitude - a.magnitude))

    const sort_by_time = () =>
        set_records(pool.slice().sort((a, b) => new Date(b.event_time).getTime() - new Date(a.event_time).getTime()))

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
        <StyledTableCell>{record_entry.file_name}</StyledTableCell>
        <StyledTableCell>{record_entry.sub_category}</StyledTableCell>
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

function RecordTable({pool}: { pool: Array<Record> }) {
    return <TableContainer component={Paper}>
        <Table sx={{minWidth: 1080}} size='small' aria-label='record-metadata'>
            <RecordTableHeader {...pool}/>
            <TableBody>
                <For each={pool}>
                    {(record_entry) => RecordEntry(record_entry)}
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

        let event_loc: Set<number> = new Set()
        let station_loc: Set<number> = new Set()

        records.forEach((record: Record) => {
            const t_event_loc = record.event_location.slice().reverse()
            const t_hash = t_event_loc[0] * t_event_loc[1]
            if (!event_loc.has(t_hash)) {
                event_loc.add(t_event_loc[0] * t_event_loc[1])
                const event_marker = L.marker(t_event_loc, {icon: GreenIcon}).addTo(marker_layer)
                event_marker.bindPopup('Event')
                x += t_event_loc[0]
                y += t_event_loc[1]
            }
            if (show_station()) {
                const t_station_loc = record.station_location.slice().reverse()
                const t_hash = t_station_loc[0] * t_station_loc[1]
                if (!station_loc.has(t_hash)) {
                    station_loc.add(t_hash)
                    const station_marker = L.marker(t_station_loc, {icon: RedIcon}).addTo(marker_layer)
                    station_marker.bindPopup('Station')
                }
            }
        })

        if (records.length > 0) {
            x /= event_loc.size
            y /= event_loc.size
        } else {
            x = 52.5068441
            y = 13.4247317
        }

        map.flyTo([x, y], 6)
    })

    return <Card id='event_map'></Card>
}

const [alignment, set_alignment] = createSignal('jp')
const [page_size, set_page_size] = createSignal(20)
const [min_mag, set_min_mag] = createSignal(0)
const [max_mag, set_max_mag] = createSignal(10)
const [min_pga, set_min_pga] = createSignal(0)
const [max_pga, set_max_pga] = createSignal(0)
const [event_lat, set_event_lat] = createSignal(0)
const [event_log, set_event_log] = createSignal(0)
const [station_lat, set_station_lat] = createSignal(0)
const [station_log, set_station_log] = createSignal(0)
const [direction, set_direction] = createSignal(null)
const [show_station, set_show_station] = createSignal(false)

async function fetch() {
    let url = alignment() ? `/${alignment()}/query` : `/query`
    url += `?page_size=${page_size() > 0 ? page_size() : 20}`
    if (min_mag() > 0) url += `&min_magnitude=${min_mag()}`
    if (max_mag() > 0 && max_mag() >= min_mag()) url += `&max_magnitude=${max_mag()}`
    if (min_pga() > 0) url += `&min_pga=${min_pga()}`
    if (max_pga() > 0 && max_pga() >= min_pga()) url += `&max_pga=${max_pga()}`
    if (direction()) url += `&direction=${direction()}`
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
            console.log(alignment())
        }}>
            <ToggleButton value='jp'>Japan</ToggleButton>
            <ToggleButton value='nz'>New Zealand</ToggleButton>
        </ToggleButtonGroup>
    );
}

const MinMag = () => {
    onMount(() => {
        tippy('#min-magnitude', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'The minimum magnitude of interest.',
        })
    })

    const [error, set_error] = createSignal(false)

    const handleChange = (event: any) => {
        const re: RegExp = /^\d+(\.\d{1,2})?$/
        const value = event.target.value
        set_error(!value.match(re))
        set_min_mag(value)
    }

    return <TextField InputLabelProps={{shrink: true}} id='min-magnitude' label='Min. Mag.' type='text'
                      value={min_mag()} error={error()} onChange={handleChange}/>
}

const MaxMag = () => {
    onMount(() => {
        tippy('#max-magnitude', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'The maximum magnitude of interest.',
        })
    })

    const [error, set_error] = createSignal(false)

    const handleChange = (event: any) => {
        const re: RegExp = /^\d+(\.\d{1,2})?$/
        const value = event.target.value
        set_error(!value.match(re))
        set_max_mag(value)
    }

    return <TextField InputLabelProps={{shrink: true}} id='max-magnitude' label='Max. Mag.' type='text'
                      value={max_mag()} error={error()} onChange={handleChange}/>
}


const MinAcc = () => {
    onMount(() => {
        tippy('#min-pga', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'The minimum PGA of interest.',
        })
    })

    const [error, set_error] = createSignal(false)

    const handleChange = (event: any) => {
        const re: RegExp = /^\d+(\.\d{1,2})?$/
        const value = event.target.value
        set_error(!value.match(re))
        set_min_pga(value)
    }

    return <TextField InputLabelProps={{shrink: true}} id='min-pga' label='Min. PGA' type='text'
                      value={min_pga()} error={error()} onChange={handleChange}/>
}

const MaxAcc = () => {
    onMount(() => {
        tippy('#max-pga', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'The maximum PGA of interest.',
        })
    })

    const [error, set_error] = createSignal(false)

    const handleChange = (event: any) => {
        const re: RegExp = /^\d+(\.\d{1,2})?$/
        const value = event.target.value
        set_error(!value.match(re))
        set_max_pga(value)
    }

    return <TextField InputLabelProps={{shrink: true}} id='max-pga' label='Max. PGA' type='text'
                      value={max_pga()} error={error()} onChange={handleChange}/>
}

const EventLat = () => {
    onMount(() => {
        tippy('#event-lat', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'The approximate latitude of the event.',
        })
    })

    const [error, set_error] = createSignal(false)

    const handleChange = (event: any) => {
        const re: RegExp = /^-?\d+(\.\d{1,2})?$/
        const value = event.target.value
        set_error(!value.match(re))
        set_event_lat(value)
    }

    return <TextField InputLabelProps={{shrink: true}} id='event-lat' label='Event Lat.' type='text'
                      value={event_lat()} error={error()} onChange={handleChange}/>
}


const EventLog = () => {
    onMount(() => {
        tippy('#event-log', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'The approximate longitude of the event.',
        })
    })

    const [error, set_error] = createSignal(false)

    const handleChange = (event: any) => {
        const re: RegExp = /^-?\d+(\.\d{1,2})?$/
        const value = event.target.value
        set_error(!value.match(re))
        set_event_log(value)
    }

    return <TextField InputLabelProps={{shrink: true}} id='event-log' label='Event Log.' type='text'
                      value={event_log()} error={error()} onChange={handleChange}/>
}

const StationLat = () => {
    onMount(() => {
        tippy('#station-lat', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'The approximate latitude of the station.',
        })
    })

    const [error, set_error] = createSignal(false)

    const handleChange = (event: any) => {
        const re: RegExp = /^-?\d+(\.\d{1,2})?$/
        const value = event.target.value
        set_error(!value.match(re))
        set_station_lat(value)
    }

    return <TextField InputLabelProps={{shrink: true}} id='station-lat' label='Station Lat.' type='text'
                      value={station_lat()} error={error()} onChange={handleChange}/>
}


const StationLog = () => {
    onMount(() => {
        tippy('#station-log', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'The approximate longitude of the station.',
        })
    })

    const [error, set_error] = createSignal(false)

    const handleChange = (event: any) => {
        const re: RegExp = /^-?\d+(\.\d{1,2})?$/
        const value = event.target.value
        set_error(!value.match(re))
        set_station_log(value)
    }

    return <TextField InputLabelProps={{shrink: true}} id='station-log' label='Station Log.' type='text'
                      value={station_log()} error={error()} onChange={handleChange}/>
}

function SearchConfig() {
    return <>
        <Grid container item xs={12}>
            <Stack component='form' spacing={1} noValidate direction='row' alignItems='center' justifyItems='center'
                   justifyContent='center' autocomplete='off'>
                <MinMag/><MaxMag/><MinAcc/><MaxAcc/>
                <EventLat/><EventLog/><StationLat/><StationLog/>
                <TextField InputLabelProps={{shrink: true}} id='event_time_from' label='From' type='datetime-local'
                           sx={{width: '360px'}}/>
                <TextField InputLabelProps={{shrink: true}} id='event_time_to' label='To' type='datetime-local'
                           sx={{width: '360px'}}/>
                <TextField InputLabelProps={{shrink: true}} id='direction' label='Direction' type='text'
                           onChange={(event: ST.ChangeEvent<HTMLInputElement>) => {
                               set_direction(event.target.value)
                           }}/>
            </Stack>
        </Grid>
        <Grid container item xs={12}>
            <Stack component='form' spacing={1} noValidate direction='row' alignItems='center' justifyItems='center'
                   justifyContent='center' autocomplete='off'>
                <TextField InputLabelProps={{shrink: true}} id='page_size' label='Records per Page' type='number'
                           defaultValue={20} onChange={(event: ST.ChangeEvent<HTMLInputElement>) => {
                    set_page_size(event.target.value)
                }}/>
                <ColorToggleButton/>
                <Button variant='contained' id='clear' onClick={fetch}><SearchIcon/></Button>
                <Switch id='show_station_location' checked={show_station()}
                        onChange={() => set_show_station(!show_station())}/>
            </Stack>
        </Grid>
    </>;
}

const SearchPage: Component = () => {
    return <Grid container spacing={1}>
        <SearchConfig/>
        <Grid container item xs={12} spacing={1}>
            <Grid item xs={12}><EventMap/></Grid>
            {records?.length > 0 && <Grid item xs={12}><RecordTable pool={records}/></Grid>}
        </Grid>
    </Grid>
}

export default SearchPage