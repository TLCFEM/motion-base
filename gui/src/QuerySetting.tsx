import FormControl from "@suid/material/FormControl";
import FormControlLabel from "@suid/material/FormControlLabel";
import Radio from "@suid/material/Radio";
import RadioGroup from "@suid/material/RadioGroup";
// @ts-ignore
import * as ST from "@suid/types";
import {createSignal, For} from "solid-js";
import FormLabel from "@suid/material/FormLabel";
import Stack from "@suid/material/Stack";
import Divider from "@suid/material/Divider";


export default function RegionGroup() {
    let region_set: Array<string> = ['jp', 'nz', 'us', 'eu']

    const [region, set_region] = createSignal(region_set[0]);

    const handle_change = (event: ST.ChangeEvent<HTMLInputElement>) => {
        set_region(event.target.value);
    };

    return (
        <FormControl>
            <FormLabel>Region</FormLabel>
            <RadioGroup aria-labelledby="region" name="region" id="region" value={region()} onChange={handle_change}>
                <Stack
                    direction='row'
                    justifyContent="center"
                    alignItems="center"
                    divider={<Divider orientation="vertical" flexItem/>}>
                    <For each={region_set}>{(r) =>
                        <FormControlLabel value={r} control={<Radio size="small"/>} label={r.toUpperCase()}/>
                    }</For>
                </Stack>
            </RadioGroup>
        </FormControl>
    );
}
