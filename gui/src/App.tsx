import type {Component} from 'solid-js';
import {createEffect, createSignal, onMount} from 'solid-js';
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
import RegionGroup from './QuerySetting';
import AppBar from '@suid/material/AppBar'
import IconButton from '@suid/material/IconButton';
import Toolbar from '@suid/material/Toolbar';
import MenuIcon from '@suid/icons-material/Menu';
import Stack from "@suid/material/Stack";
import {jackpot} from './API';
import styled from "@suid/material/styles/styled";
import Paper from "@suid/material/Paper";

const [event_location, set_event_location] = createSignal([52.5068441, 13.4247317]);
const [station_location, set_station_location] = createSignal([52.5068441, 13.4247317]);


const axis_label = (label: string, size: number) => {
    return {
        title: {
            text: label,
            font: {
                size: size,
                color: '#548861'
            }
        },
    }
}

export const plot = (data: any) => {
    set_event_location([data.latitude, data.longitude]);
    set_station_location([data.station_latitude, data.station_longitude]);

    const interval: number = data.interval;

    let x: Array<number> = [];
    for (let i = 0; i < data.data.length; i++) x.push(i * interval);

    let trace = {x: x, y: data.data, type: 'scatter', name: data.file_name};

    Plotly.newPlot(document.getElementById('canvas'), [trace], {
        autosize: true,
        automargin: true,
        title: {text: data.file_name, font: {size: 24},},
        xaxis: axis_label('Time (s)', 18),
        yaxis: axis_label('Amplitude (cm/s^2)', 18),
    }, {responsive: true,});

    return null;
}

const Item = styled(Paper)(({theme}) => ({
    ...theme.typography.body2,
    padding: theme.spacing(1),
    textAlign: 'center',
    color: theme.palette.text.secondary,
}));

const App: Component = () => {
    let map: L.Map;
    let event_marker: L.Marker;
    let station_marker: L.Marker;

    onMount(() => {
        map = L.map('map').setView(event_location(), 6);

        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 12,
            attribution: '© OpenStreetMap'
        }).addTo(map);

        event_marker = L.marker(event_location()).addTo(map);
        station_marker = L.marker(station_location()).addTo(map);
        event_marker.bindPopup('event location');
        station_marker.bindPopup('station location');

        tippy('#random', {
            arrow: true,
            animation: 'scale',
            inertia: true,
            theme: 'translucent',
            content: 'Get A Random Waveform!',
        });

        jackpot();
    })

    createEffect(() => {
        event_marker.setLatLng(event_location());
        station_marker.setLatLng(station_location());

        map.flyTo(event_location(), 5);
    });

    return (
        <>
            <AppBar position='static' id='app-bar'>
                <Toolbar>
                    <IconButton size='medium' edge='start' color='inherit' aria-label='menu' sx={{mr: 2}}>
                        <MenuIcon/>
                    </IconButton>
                    <Typography variant='h5' component='div' sx={{flexGrow: 2}}>
                        Motion Base
                    </Typography>
                    <Stack spacing={2} direction="row">
                        <Button variant='contained' id='random' onClick={jackpot}>Roll</Button>
                        <Button variant='contained' id='login'>Login</Button>
                    </Stack>
                </Toolbar>
            </AppBar>
            <Stack spacing={2} direction="row">
                <Item><RegionGroup/></Item>
            </Stack>
        </>
    );
};

export default App;
