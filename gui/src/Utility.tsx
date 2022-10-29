// @ts-ignore
import L from 'leaflet'
import styled from "@suid/material/styles/styled";
import Paper from "@suid/material/Paper";
import TableCell, {tableCellClasses} from "@suid/material/TableCell";
import TableRow from "@suid/material/TableRow";
import {createEffect} from "solid-js";
// @ts-ignore
import Plotly from 'plotly.js-dist-min'

const LeafIcon = L.Icon.extend({
    options: {
        iconSize: [38, 95],
        shadowSize: [50, 64],
        iconAnchor: [22, 94],
        shadowAnchor: [4, 62],
        popupAnchor: [-3, -76]
    }
})

export const RedIcon = new LeafIcon({
    iconUrl: 'http://leafletjs.com/examples/custom-icons/leaf-red.png',
    shadowUrl: 'http://leafletjs.com/examples/custom-icons/leaf-shadow.png'
})

export const GreenIcon = new LeafIcon({
    iconUrl: 'http://leafletjs.com/examples/custom-icons/leaf-green.png',
    shadowUrl: 'http://leafletjs.com/examples/custom-icons/leaf-shadow.png'
})


export function DefaultMap(container: string, centre: number[]) {
    let map: L.Map

    map = L.map(document.getElementById(container)).setView(centre, 6)

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 12, attribution: '© OpenStreetMap'
    }).addTo(map)
    return map
}

export class Record {
    public id: string = ''
    public file_name: string = ''
    public sub_category: string = ''
    public magnitude: number = 0
    public origin_time: string = ''
    public event_location: Array<number> = [13.4247317, 52.5068441]
    public depth: number = 0
    public station_code: string = ''
    public station_location: Array<number> = [13.4247317, 52.5068441]
    public sampling_frequency: number = 0
    public sampling_frequency_unit: string = ''
    public duration: number = 0
    public direction: string = ''
    public maximum_acceleration: number = 0

    public interval: number = 0
    public data: Array<number> = Array<number>(0)

    public upsampled_interval: number = 0
    public upsampled_data: Array<number> = Array<number>(0)

    public frequency: number = 0
    public spectrum: Array<number> = Array<number>(0)

    public upsampled_frequency: number = 0
    public upsampled_spectrum: Array<number> = Array<number>(0)

    // response spectrum related
    public period: Array<number> = Array<number>(0)
    public SA: Array<number> = Array<number>(0)
    public SV: Array<number> = Array<number>(0)
    public SD: Array<number> = Array<number>(0)

    public constructor(data: any) {
        Object.assign(this, data)
    }
}

export const Item = styled(Paper)(({theme}) => ({
    backgroundColor: theme.palette.mode === 'dark' ? '#1A2027' : '#fff',
    ...theme.typography.body2,
    padding: theme.spacing(1),
    textAlign: 'center',
    color: theme.palette.text.secondary,
}))

export const StyledTableCell = styled(TableCell)(({theme}) => ({
    [`&.${tableCellClasses.head}`]: {
        backgroundColor: theme.palette.primary.main, // backgroundColor: theme.palette.common.black,
        color: theme.palette.common.white,
    }, [`&.${tableCellClasses.body}`]: {
        fontSize: 14,
    },
}))

export const StyledTableRow = styled(TableRow)(({theme}) => ({
    '&:nth-of-type(odd)': {
        backgroundColor: theme.palette.action.hover,
    }, '&:last-child td, &:last-child th': {
        border: 0,
    },
}))

export const axis_label = (label: string, size: number) => {
    return {
        title: {
            text: label, font: {
                size: size, color: '#1f78b4'
            }
        },
    }
}

export function ResponseSpectrum(record_entry: Record, spectrum_type: string, element_id: string) {
    createEffect(() => {
        let target: Array<number> = Array<number>(0)
        let unit: string = ''
        if (spectrum_type === 'SD') {
            target = record_entry.SD
            unit = 'cm/s/s'
        } else if (spectrum_type === 'SV') {
            target = record_entry.SV
            unit = 'cm/s'
        } else if (spectrum_type === 'SA') {
            target = record_entry.SA
            unit = 'cm'
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

    return <Item id={element_id}></Item>
}
