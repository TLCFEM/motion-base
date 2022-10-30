import {createEffect} from "solid-js";
import {axis_label} from "./Utility";
// @ts-ignore
import Plotly from 'plotly.js-dist-min'
import Card from "@suid/material/Card";

export function ResponseSpectrum(data: Array<object>, spectrum_type: string, element_id: string) {
    createEffect(() => {
        let unit: string = ''
        if (spectrum_type === 'SD') unit = 'cm'
        else if (spectrum_type === 'SV') unit = 'cm/s'
        else if (spectrum_type === 'SA') unit = 'Gal'

        Plotly.newPlot(document.getElementById(element_id),
            data,
            {
                autosize: true,
                margin: {l: 60, r: 60, b: 60, t: 60, pad: 0},
                automargin: true,
                title: {text: `${spectrum_type} (5% damping)`, font: {size: 14},},
                xaxis: axis_label('Period (s)', 12),
                yaxis: axis_label(`Amplitude (${unit})`, 12),
                showlegend: true,
                legend: {
                    x: 1,
                    xanchor: 'right',
                    y: 1
                }
            }, {responsive: true,})
    })

    return <Card id={element_id}></Card>
}