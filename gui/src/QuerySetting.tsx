import FormControl from "@suid/material/FormControl";
import FormControlLabel from "@suid/material/FormControlLabel";
import FormLabel from "@suid/material/FormLabel";
import Radio from "@suid/material/Radio";
import RadioGroup from "@suid/material/RadioGroup";
// @ts-ignore
import * as ST from "@suid/types";
import {createSignal} from "solid-js";

export default function RegionGroup() {
    const [value, setValue] = createSignal("jp");

    const handleChange = (event: ST.ChangeEvent<HTMLInputElement>) => {
        setValue(event.target.value);
    };

    return (
        <FormControl>
            <FormLabel id="region">Region</FormLabel>
            <RadioGroup
                aria-labelledby="region"
                name="region-selector"
                id="region-selector"
                value={value()}
                onChange={handleChange}
            >
                <FormControlLabel value="jp" control={<Radio/>} label="JP"/>
                <FormControlLabel value="nz" control={<Radio/>} label="NZ"/>
            </RadioGroup>
        </FormControl>
    );
}
