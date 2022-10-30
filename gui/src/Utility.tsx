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

export function set_response_spectrum(record: Record, data: Array<Array<number>>) {
    record.period = data.map((d: Array<number>) => d[0])
    record.SD = data.map((d: Array<number>) => d[1])
    record.SV = data.map((d: Array<number>) => d[2])
    record.SA = data.map((d: Array<number>) => d[3])
}