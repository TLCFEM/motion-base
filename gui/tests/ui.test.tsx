import { cleanup, fireEvent, render, screen } from "@solidjs/testing-library";
import { createSignal } from "solid-js";
import { afterEach, describe, expect, it } from "vitest";
import { CheckboxField, ErrorDialog, TextField } from "../src/ui";

afterEach(cleanup);

describe("TextField", () => {
    it("renders its label and reports typed values", () => {
        const [value, setValue] = createSignal("");

        render(() => <TextField label="Station Code" value={value()} onValueChange={setValue} />);

        const input = screen.getByLabelText("Station Code") as HTMLInputElement;
        fireEvent.input(input, { target: { value: "WTMC" } });

        expect(value()).toBe("WTMC");
    });
});

describe("CheckboxField", () => {
    it("toggles through the Ark checkbox primitive", async () => {
        const [checked, setChecked] = createSignal(false);

        render(() => <CheckboxField label="Map" checked={checked()} onCheckedChange={setChecked} />);

        const checkbox = screen.getByRole("checkbox") as HTMLInputElement;

        fireEvent.click(checkbox);
        await new Promise((resolve) => setTimeout(resolve, 0));
        expect(checked()).toBe(true);

        fireEvent.click(checkbox);
        await new Promise((resolve) => setTimeout(resolve, 0));
        expect(checked()).toBe(false);
    });
});

describe("ErrorDialog", () => {
    it("shows the error message when open", () => {
        render(() => <ErrorDialog open={true} message="Backend unavailable" onClose={() => undefined} />);

        expect(screen.getByText("Backend unavailable")).toBeTruthy();
    });
});
