import { cleanup, fireEvent, render, screen } from "@solidjs/testing-library";
import { afterEach, describe, expect, it } from "vitest";
import { SeismicRecord } from "../src/api";
import { QueryTable } from "../src/Query";

afterEach(cleanup);

const tick = () => new Promise((resolve) => setTimeout(resolve, 0));

const record = (index: number) =>
    new SeismicRecord({
        id: `record-${index}`,
        magnitude: index === 0 ? 9 : 1,
        station_code: "wtmc",
        direction: "ew",
        event_location: [0, 0],
        station_location: [0, 0],
    });

const setup = (count: number) => {
    const records = Array.from({ length: count }, (_, index) => record(index));
    const view = render(() => <QueryTable records={records} onSelect={() => undefined} />);
    const ids = () => [...view.container.querySelectorAll("tbody tr td:first-child")].map((cell) => cell.textContent);
    return { ...view, ids };
};

describe("QueryTable pagination", () => {
    it("paginates the fetched records at ten rows per page", () => {
        const { container, ids } = setup(500);

        expect(container.querySelectorAll("tbody tr")).toHaveLength(10);
        expect(ids()[0]).toBe("record-0");
        expect(screen.getByText("10 / page")).toBeTruthy();
        expect(screen.getByText("· 500 fetched")).toBeTruthy();
        expect(screen.getByText("1 / 50")).toBeTruthy();
    });

    it("reaches every fetched record through the table pages", async () => {
        const { container, ids } = setup(500);

        fireEvent.click(screen.getByTitle("Next page"));
        await tick();
        expect(ids()[0]).toBe("record-10");
        expect(screen.getByText("2 / 50")).toBeTruthy();

        fireEvent.click(screen.getByTitle("Last page"));
        await tick();
        expect(container.querySelectorAll("tbody tr")).toHaveLength(10);
        expect(ids()[0]).toBe("record-490");
    });

    it("changes the table page size without refetching", async () => {
        const { container, ids } = setup(500);

        fireEvent.click(screen.getByLabelText("More rows per page"));
        await tick();
        expect(container.querySelectorAll("tbody tr")).toHaveLength(11);
        expect(ids()[0]).toBe("record-0");
        expect(screen.getByText("11 / page")).toBeTruthy();

        fireEvent.click(screen.getByTitle("Last page"));
        await tick();
        expect(ids()[0]).toBe("record-495");
        expect(container.querySelectorAll("tbody tr")).toHaveLength(5);
    });

    it("sorts all fetched records while keeping the table page size", async () => {
        const { container, ids } = setup(60);

        const header = [...container.querySelectorAll("th")].find((cell) => cell.textContent?.includes("Magnitude"));
        header?.click();
        await tick();

        expect(container.querySelectorAll("tbody tr")).toHaveLength(10);
        expect(ids()[0]).toBe("record-0");
    });
});
