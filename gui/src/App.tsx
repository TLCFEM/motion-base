import type {Component} from 'solid-js';
import {createSignal} from "solid-js";
import axios from "axios";
import Plotly from 'plotly.js-dist-min';

axios.defaults.baseURL = 'http://127.0.0.1:8000';

const getBasicInfo = () => {
    const [info, setInfo] = createSignal(null);
    axios.get('/alive').then(res => res.data.message).then(setInfo);
    return info;
}

const plot = () => {
    let canvas = document.getElementById('canvas');
    axios.get('/jp/waveform/jackpot').then(res => {
        let interval = res.data.interval;

        let x = [];
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
            margin: {t: 0},
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
        }, {responsive: true});
    });
    return null;
}

const App: Component = () => {
    return (
        <div>
            <h1>Motion Base</h1>
            <p>{getBasicInfo()}</p>
            {plot()}
        </div>
    );
};

export default App;
