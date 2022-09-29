import type {Component} from 'solid-js';
import {createEffect, createRoot, createSignal, onMount} from "solid-js";
import axios from "axios";
// @ts-ignore
import Plotly from 'plotly.js-dist-min';
import tippy from 'tippy.js';
import 'tippy.js/dist/tippy.css';
import 'tippy.js/themes/material.css';
import 'tippy.js/animations/scale.css';
import Button from "@suid/material/Button";
import Typography from "@suid/material/Typography"
import 'leaflet/dist/leaflet.css';
// @ts-ignore
import L from 'leaflet';
import RegionGroup from "./QuerySetting";
import Paper from "@suid/material/Paper";
import styled from "@suid/material/styles/styled";
import AppBar from "@suid/material/AppBar"
import IconButton from "@suid/material/IconButton";
import Toolbar from "@suid/material/Toolbar";
import MenuIcon from "@suid/icons-material/Menu";
import {jackpot} from "./API";

axios.defaults.baseURL = 'http://127.0.0.1:8000';

const [event_location, set_event_location] = createSignal([52.5068441, 13.4247317]);
const [station_location, set_station_location] = createSignal([52.5068441, 13.4247317]);

createRoot(() => {
    const map = L.map('map').setView(event_location(), 8);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 15,
        attribution: '© OpenStreetMap'
    }).addTo(map);

    let event_marker = L.marker(event_location()).addTo(map);
    let station_marker = L.marker(station_location()).addTo(map);

    event_marker.bindPopup('event location');
    station_marker.bindPopup('station location');

    createEffect(() => {
        event_marker.setLatLng(event_location());
        station_marker.setLatLng(station_location());

        map.flyTo(event_location(), 5);
    });
});


const axis_label = (label: string, size: number) => {
    return {
        title: {
            text: label,
            font: {
                size: size,
                color: '#812618'
            }
        },
    }
}


export const plot = (data: any) => {
    let canvas = document.getElementById('canvas');

    set_event_location([data.latitude, data.longitude]);
    set_station_location([data.station_latitude, data.station_longitude]);

    let interval: number = data.interval;

    let x: Array<number> = [];
    for (let i = 0; i < data.data.length; i++) {
        x.push(i * interval);
    }

    let trace = {
        x: x,
        y: data.data,
        type: 'scatter',
        name: data.file_name
    };
    Plotly.newPlot(canvas, [trace], {
        autosize: true,
        automargin: true,
        title: {
            text: data.file_name,
            font: {
                size: 24
            },
        },
        xaxis: axis_label('Time (s)', 18),
        yaxis: axis_label('Amplitude (cm/s^2)', 18),
    }, {
        responsive: true,
    });

    return null;
}

const Item = styled(Paper)(({theme}) => ({
    ...theme.typography.body2,
    padding: theme.spacing(1),
    textAlign: "center",
    color: theme.palette.text.secondary,
}));

const App: Component = () => {
    onMount(() => {
        tippy('#refresh', {
            arrow: true,
            animation: 'shift-toward',
            inertia: true,
            theme: 'material',
            content: 'Get a new random waveform!',
        });
    });

    return (
        <div>
            <AppBar position="static">
                <Toolbar>
                    <IconButton size="medium" edge="start" color="inherit" aria-label="menu" sx={{mr: 2}}>
                        <MenuIcon/>
                    </IconButton>
                    <Typography variant="h5" component="div" sx={{flexGrow: 2}}>
                        Motion Base
                    </Typography>
                    <Button variant="outlined">Login</Button>
                    <Button variant="contained" id="refresh" onClick={jackpot}>Refresh</Button>
                </Toolbar>
            </AppBar>
            {jackpot()}
            <Item id='high'><RegionGroup/></Item>
        </div>
    );
};

export default App;
