import type {Component} from 'solid-js';
import {createSignal} from "solid-js";
import axios from "axios";
// @ts-ignore
import Plotly from 'plotly.js-dist-min';
import tippy from 'tippy.js';
import 'tippy.js/dist/tippy.css';
import 'tippy.js/themes/material.css';
import 'tippy.js/animations/scale.css';
import Button from "@suid/material/Button";
import 'leaflet/dist/leaflet.css';
// @ts-ignore
import L from 'leaflet';

axios.defaults.baseURL = 'http://127.0.0.1:8000';

let map = L.map('map').setView([42.35, -71.08], 13);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap'
}).addTo(map);

const getBasicInfo = () => {
    const [info, setInfo] = createSignal(null);
    axios.get('/alive').then(res => res.data.message).then(setInfo);
    return info;
}

const plot = () => {
    let canvas = document.getElementById('canvas');
    axios.get('/jp/waveform/jackpot').then(res => {
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
            xaxis: {
                title: {
                    text: 'Time (s)',
                    font: {
                        size: 16,
                        color: '#812618'
                    }
                },
            },
            yaxis: {
                title: {
                    text: 'Amplitude',
                    font: {
                        size: 16,
                        color: '#812618'
                    }
                }
            }
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

const App: Component = () => {
    return (
        <div>
            <Button variant="contained" id="refresh" onClick={plot}>Refresh</Button>
            <h1>Motion Base</h1>
            <p>{getBasicInfo()}</p>
            {plot()}
        </div>
    );
};

export default App;
