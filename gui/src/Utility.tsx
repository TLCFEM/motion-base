// @ts-ignore
import L from 'leaflet'
import styled from "@suid/material/styles/styled";
import Paper from "@suid/material/Paper";
import TableCell, {tableCellClasses} from "@suid/material/TableCell";
import TableRow from "@suid/material/TableRow";

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

    public time_interval: number = 0
    public waveform: Array<number> = Array<number>(0)

    public frequency_interval: number = 0
    public spectrum: Array<number> = Array<number>(0)

    // response spectrum related
    public period: Array<number> = Array<number>(0)
    public displacement_spectrum: Array<number> = Array<number>(0)
    public velocity_spectrum: Array<number> = Array<number>(0)
    public acceleration_spectrum: Array<number> = Array<number>(0)

    public constructor(data: any) {
        Object.assign(this, data)
    }

    public extract_waveform(name: string) {
        if (this.id === '') return {}
        return {
            x: Array<number>(this.waveform?.length).fill(0).map((_, i) => i * this.time_interval),
            y: this.waveform,
            type: 'scatter', name: name
        }
    }

    public extract_spectrum(name: string) {
        if (this.id === '') return {}
        return {
            x: Array<number>(this.spectrum?.length).fill(0).map((_, i) => i * this.frequency_interval),
            y: this.spectrum,
            type: 'scatter', name: name
        }
    }

    public extract_response_spectrum(name: string, kind: string) {
        if (this.id === '') return {}

        if (kind === 'SA') return {
            x: this.period,
            y: this.acceleration_spectrum,
            type: 'scatter', name: name
        }
        if (kind === 'SV') return {
            x: this.period,
            y: this.velocity_spectrum,
            type: 'scatter', name: name
        }

        return {
            x: this.period,
            y: this.displacement_spectrum,
            type: 'scatter', name: name
        }
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

export function extract_waveform(record: Record | undefined, name: string) {
    if (!record || record.id === '') return {}
    return {
        x: Array<number>(record.waveform?.length).fill(0).map((_, i) => i * record.time_interval),
        y: record.waveform,
        type: 'scatter', name: name
    }
}

export function extract_spectrum(record: Record | undefined, name: string) {
    if (!record || record.id === '') return {}
    return {
        x: Array<number>(record.spectrum?.length).fill(0).map((_, i) => i * record.frequency_interval),
        y: record.spectrum,
        type: 'scatter', name: name
    }
}

export function extract_response_spectrum(record: Record | undefined, name: string, kind: string) {
    if (!record || record.id === '') return {}

    if (kind === 'SA') return {
        x: record.period,
        y: record.acceleration_spectrum,
        type: 'scatter', name: name
    }
    if (kind === 'SV') return {
        x: record.period,
        y: record.velocity_spectrum,
        type: 'scatter', name: name
    }

    return {
        x: record.period,
        y: record.displacement_spectrum,
        type: 'scatter', name: name
    }
}