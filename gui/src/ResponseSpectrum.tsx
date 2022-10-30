import {createEffect} from "solid-js";
import {axis_label, Record} from "./Utility";
// @ts-ignore
import Plotly from 'plotly.js-dist-min'
import Card from "@suid/material/Card";

export function ResponseSpectrum(record_entry: Record, spectrum_type: string, element_id: string) {
    createEffect(() => {
        let target: Array<number> = Array<number>(0)
        let unit: string = ''
        if (spectrum_type === 'SD') {
            target = record_entry.SD
            unit = 'cm'
        } else if (spectrum_type === 'SV') {
            target = record_entry.SV
            unit = 'cm/s'
        } else if (spectrum_type === 'SA') {
            target = record_entry.SA
            unit = 'Gal'
        }

        Plotly.react(document.getElementById(element_id),
            [{x: record_entry.period, y: target, type: 'scatter', name: `${spectrum_type} (5% damping)`}],
            {
                autosize: true,
                margin: {l: 60, r: 60, b: 60, t: 60, pad: 0},
                automargin: true,
                title: {text: `${spectrum_type} (5% damping)`, font: {size: 14},},
                xaxis: Object.assign({}, axis_label('Period (s)', 12), {range: [0, record_entry.period[record_entry.period.length - 1]]}),
                yaxis: Object.assign({}, axis_label(`Amplitude (${unit})`, 12), {range: [0, Math.max(...target) * 1.1]}),
                showlegend: false,
                legend: {
                    x: 1,
                    xanchor: 'right',
                    y: 1
                }
            }, {responsive: true,})
    })

    return <Card id={element_id}></Card>
}