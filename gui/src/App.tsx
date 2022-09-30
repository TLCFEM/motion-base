import type {Component} from 'solid-js';
import {createEffect, createSignal, For, mapArray, onMount} from 'solid-js';
// @ts-ignore
import Plotly from 'plotly.js-dist-min';
import tippy from 'tippy.js';
import 'tippy.js/dist/tippy.css';
import 'tippy.js/themes/translucent.css';
import 'tippy.js/animations/scale.css';
import Button from '@suid/material/Button';
import Typography from '@suid/material/Typography'
import 'leaflet/dist/leaflet.css';
// @ts-ignore
import L from 'leaflet';
import AppBar from '@suid/material/AppBar'
import IconButton from '@suid/material/IconButton';
import Toolbar from '@suid/material/Toolbar';
import MenuIcon from '@suid/icons-material/Menu';
import Stack from "@suid/material/Stack";
import styled from "@suid/material/styles/styled";
import Paper from "@suid/material/Paper";
import axios from "axios";
import FormControl from '@suid/material/FormControl';
import FormControlLabel from '@suid/material/FormControlLabel';
import Radio from '@suid/material/Radio';
import RadioGroup from '@suid/material/RadioGroup';
// @ts-ignore
import * as ST from '@suid/types';
import Divider from '@suid/material/Divider';
import CasinoIcon from '@suid/icons-material/Casino';
import DeleteOutlineIcon from '@suid/icons-material/DeleteOutline';
import LoginIcon from '@suid/icons-material/Login';
import Table from '@suid/material/Table';
import TableBody from '@suid/material/TableBody';
import TableContainer from '@suid/material/TableContainer';
import TableHead from '@suid/material/TableHead';
import TableRow from '@suid/material/TableRow';
import TableCell, {tableCellClasses} from '@suid/material/TableCell';
import Container from "@suid/material/Container";

const Item = styled(Paper)(({theme}) => ({
    ...theme.typography.body2, padding: theme.spacing(1), textAlign: 'center', color: theme.palette.text.secondary,
}));


const PaddingPaper = styled(Paper)(({theme}) => ({
    ...theme.typography.body2,
    // marginBottom: theme.spacing(1),
    // marginTop: theme.spacing(1),
    // padding: theme.spacing(1),
    textAlign: 'center',
    color: theme.palette.text.secondary,
}));


let region_set: Array<string> = ['jp', 'nz', 'us', 'eu']

const [region, set_region] = createSignal(region_set[0]);

function RegionGroup() {
    const handle_change = (event: ST.ChangeEvent<HTMLInputElement>) => {
        set_region(event.target.value);
    };

    return (<FormControl>
        <RadioGroup aria-labelledby='region' name='region' id='region' value={region()} onChange={handle_change}>
            <Stack
                direction='row'
                justifyContent='center'
                alignItems='center'
                divider={<Divider orientation='vertical' flexItem/>}>
                <For each={region_set}>
                    {(r) => <FormControlLabel value={r} control={<Radio size='small'/>} label={r.toUpperCase()}/>}
                </For>
            </Stack>
        </RadioGroup>
    </FormControl>);
}

const [event_location, set_event_location] = createSignal([52.5068441, 13.4247317]);
const [station_location, set_station_location] = createSignal([52.5068441, 13.4247317]);
const [waveform, set_waveform] = createSignal([Array<number>(0), Array<number>(0), '']);

class Record {
    public id: string = '';
    public file_name: string = '';
    public sub_category: string = '';
    public magnitude: number = 0;
    public origin_time: string = '';
    public latitude: number = 52.5068441;
    public longitude: number = 13.4247317;
    public depth: number = 0;
    public depth_unit: string = '';
    public station_code: string = '';
    public station_latitude: number = 52.5068441;
    public station_longitude: number = 13.4247317;
    public sampling_frequency: number = 0;
    public sampling_frequency_unit: string = '';
    public duration: number = 0;
    public duration_unit: string = '';
    public direction: string = '';

    public interval: number = 0;
    public data: Array<number> = Array<number>(0);

    public constructor(data: any) {
        Object.assign(this, data);
    }
}

const [record_metadata, set_record_metadata] = createSignal<Array<Record>>(Array<Record>(0));
const [current_record, set_current_record] = createSignal<Record>(new Record({}));

const StyledTableCell = styled(TableCell)(({theme}) => ({
    [`&.${tableCellClasses.head}`]: {
        backgroundColor: theme.palette.primary.main,
        // backgroundColor: theme.palette.common.black,
        color: theme.palette.common.white,
    },
    [`&.${tableCellClasses.body}`]: {
        fontSize: 14,
    },
}));

const StyledTableRow = styled(TableRow)(({theme}) => ({
    '&:nth-of-type(odd)': {
        backgroundColor: theme.palette.action.hover,
    },
    '&:last-child td, &:last-child th': {
        border: 0,
    },
}));

function RecordTableHeader() {
    const table_header: Array<string> = ['ID', 'File Name', 'Category', 'Mw', 'Event Time', 'Depth', 'Station Code', 'Sampling Frequency', 'Duration', 'Direction']

    return <TableHead>
        <TableRow>
            <For each={table_header}>
                {(h) => {
                    if (h === 'ID')
                        return <StyledTableCell id={'table-header-id'}>{h}</StyledTableCell>
                    return <StyledTableCell>{h}</StyledTableCell>
                }}
            </For>
        </TableRow>
    </TableHead>
}

const select_record = (event: ST.ChangeEvent<HTMLInputElement>) => {
    if (event.target.tagName != 'TH') return;

    for (let i = 0; i < record_metadata().length; i++) {
        if (record_metadata()[i].id == event.target.innerText) {
            set_current_record(record_metadata()[i]);
            break;
        }
    }
}

function RecordEntry(record_entry: Record) {
    let convert_time = (time: string) => {
        if (time === '') return '';
        let date = new Date(time);
        return date.toLocaleString('en-GB');
    };

    return <StyledTableRow>
        <StyledTableCell component="th" scope="row" onClick={select_record}>{record_entry.id}</StyledTableCell>
        <StyledTableCell>{record_entry.file_name}</StyledTableCell>
        <StyledTableCell>{record_entry.sub_category}</StyledTableCell>
        <StyledTableCell>{record_entry.magnitude}</StyledTableCell>
        <StyledTableCell>{convert_time(record_entry.origin_time)}</StyledTableCell>
        <StyledTableCell>{record_entry.depth} {record_entry.depth_unit}</StyledTableCell>
        <StyledTableCell>{record_entry.station_code}</StyledTableCell>
        <StyledTableCell>{record_entry.sampling_frequency} {record_entry.sampling_frequency_unit}</StyledTableCell>
        <StyledTableCell>{record_entry.duration} {record_entry.duration_unit}</StyledTableCell>
        <StyledTableCell>{record_entry.direction}</StyledTableCell>
    </StyledTableRow>
}

function RecordTableBody() {
    return <TableBody>
        {mapArray(record_metadata, (record_entry) => <RecordEntry  {...record_entry}/>)}
    </TableBody>
}

function RecordTable() {
    return <TableContainer component={Paper}>
        <Table sx={{minWidth: 1080}} size="small" aria-label="record-metadata">
            <RecordTableHeader/>
            <RecordTableBody/>
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
    set_record_metadata(Array<Record>(0));
}


async function jackpot() {
    let region_value = region();
    if (region_value === 'us' || region_value === 'eu') region_value = 'jp';
    const url = `/${region_value}/waveform/jackpot`;
    await axios.get(url).then(res => {
        let new_record = new Record(res.data);
        set_current_record(new_record);
        set_record_metadata(record_metadata().concat(new_record));
    }).catch(err => {
        console.log(err);
    });
}


const Epicenter: Component = () => {
    let map: L.Map;
    let event_marker: L.Marker;
    let station_marker: L.Marker;

    onMount(() => {
        map = L.map(document.getElementById('epicenter')).setView(event_location(), 6);

        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 12,
            attribution: '© OpenStreetMap'
        }).addTo(map);

        event_marker = L.marker(event_location()).addTo(map);
        station_marker = L.marker(station_location()).addTo(map);

        event_marker.bindPopup('event location');
        station_marker.bindPopup('station location');

        jackpot().then();
    })

    createEffect(() => {
        event_marker.setLatLng(event_location());
        station_marker.setLatLng(station_location());

        map.flyTo(event_location(), 6);
    });

    createEffect(() => {
        const metadata = current_record();

        set_event_location([metadata.latitude, metadata.longitude]);
        set_station_location([metadata.station_latitude, metadata.station_longitude]);

        const interval: number = metadata.interval;

        let x: Array<number> = [];
        for (let i = 0; i < metadata.data.length; i++) x.push(i * interval);

        set_waveform([x, metadata.data, metadata.file_name]);
    })

    return <div id='epicenter'></div>;
}


const Waveform: Component = () => {
    createEffect(() => {
        const trace = {x: waveform()[0], y: waveform()[1], type: 'scatter', name: waveform()[2]};

        Plotly.newPlot(document.getElementById('canvas'), [trace], {
            autosize: true,
            automargin: true,
            title: {text: waveform()[2], font: {size: 20},},
            xaxis: axis_label('Time (s)', 14),
            yaxis: axis_label('Amplitude (Gal)', 14),
        }, {responsive: true,});
    })

    return <div id='canvas'></div>;
}

const login = () => {
}

const ButtonStack: Component = () => {
    onMount(() => {
        tippy('#random', {
            arrow: true, animation: 'scale', inertia: true, theme: 'translucent', content: 'Get A Random Waveform!',
        });
        tippy('#login', {
            arrow: true, animation: 'scale', inertia: true, theme: 'translucent', content: 'Login to Upload!',
        });
        tippy('#table-header-id', {
            arrow: true, animation: 'scale', inertia: true, theme: 'translucent', content: 'Click Target ID to Replot!',
        });
    })

    return <Stack spacing={2} direction="row">
        <Button variant='contained' id='random' onClick={jackpot}><CasinoIcon/></Button>
        <Button variant='contained' id='clear' onClick={clear}><DeleteOutlineIcon/></Button>
        <Button variant='contained' id='login' onClick={login}><LoginIcon/></Button>
    </Stack>
}

const Header = () => {
    return <AppBar position='static' id='app-bar' component={Paper}>
        <Toolbar>
            <IconButton size='medium' edge='start' color='inherit' aria-label='menu' sx={{mr: 2}}>
                <MenuIcon/>
            </IconButton>
            <Typography variant='h5' component='div' sx={{flexGrow: 2}}>
                Motion Base
            </Typography>
            <ButtonStack/>
        </Toolbar>
    </AppBar>
}

const App: Component = () => {
    return (<>
        <Container maxWidth='xl' sx={{my: 1}}>
            <Header/>
        </Container>
        <Container maxWidth='xl' sx={{my: 1}}>
            <Stack spacing={1} justifyContent='flex-end' direction='row'>
                <Item><RegionGroup/></Item>
            </Stack>
        </Container>
        <Container maxWidth='xl' sx={{my: 1}} style='min-height:400px'>
            <Waveform/>
            <Epicenter/>
        </Container>
        <Container maxWidth='xl' sx={{my: 1}}>
            <RecordTable/>
        </Container>
    </>);
};

export default App;
