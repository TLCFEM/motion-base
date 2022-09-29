import axios from "axios";
import {plot} from "./App";


export const jackpot = () => {
    const region = document.querySelector('[name="region"]:checked');
    let region_value = region?.getAttribute('value');
    if (region_value === undefined) {
        region_value = 'jp';
    }
    const url = `/${region_value}/waveform/jackpot`;
    axios.get(url).then(res => {
        plot(res.data)
    });

    return null;
}