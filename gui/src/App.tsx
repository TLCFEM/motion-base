import type {Component} from 'solid-js';
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
import Stack from "@suid/material/Stack";

axios.defaults.baseURL = 'http://127.0.0.1:8000';

let position: Array<number> = [42.35, -71.08];
let station_position: Array<number> = position;
let map = L.map('map').setView(position, 8);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap'
}).addTo(map);

let event_location = L.marker(position).addTo(map);
let station_location = L.marker(station_position).addTo(map);

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


const plot = () => {
    let canvas = document.getElementById('canvas');
    let region = document.querySelector('[name="region-selector"]:checked');
    let region_value = region?.getAttribute('value');
    if (region_value === undefined) {
        region_value = 'jp';
    }
    let url = `/${region_value}/waveform/jackpot`;
    axios.get(url).then(res => {
        position = [res.data.latitude, res.data.longitude];
        station_position = [res.data.station_latitude, res.data.station_longitude];
        event_location.remove();
        station_location.remove();
        map.flyTo(position, 5);
        event_location = L.marker(position).addTo(map);
        station_location = L.marker(station_position).addTo(map);
        event_location.bindPopup('event location');
        station_location.bindPopup('station location');

        let interval: number = res.data.interval;

        let x: Array<number> = [];
        for (let i = 0; i < res.data.data.length; i++) {
            x.push(i * interval);
        }

        let trace = {
            x: x,
            y: res.data.data,
            type: 'scatter',
            name: res.data.file_name
        };
        Plotly.newPlot(canvas, [trace], {
            autosize: true,
            automargin: true,
            title: {
                text: res.data.file_name,
                font: {
                    size: 24
                },
            },
            xaxis: axis_label('Time (s)', 18),
            yaxis: axis_label('Amplitude (cm/s^2)', 18),
        }, {
            responsive: true,
        });
    });

    tippy('#refresh', {
        arrow: true,
        animation: 'shift-toward',
        inertia: true,
        theme: 'material',
        content: 'Get a new random waveform!',
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
    return (
        <div id="high">
            <Typography variant="h3">Motion Base</Typography>
            <Stack spacing={2} id="setting">
                <Item>
                    <Button variant="contained" id="refresh" onClick={plot}>Refresh</Button>
                    <Button variant="contained">Hello</Button>
                    <Button variant="contained">World</Button>
                </Item>
                <Item><RegionGroup/></Item>
            </Stack>
            {plot()}
        </div>
    )
        ;
};

export default App;
