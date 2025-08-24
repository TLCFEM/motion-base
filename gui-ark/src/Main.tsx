import {Tabs} from '@ark-ui/solid/tabs'
import {createSignal, onMount} from "solid-js";
import {marked} from "marked";
import hljs from "highlight.js";


const Brief = () => {
    const [html, setHtml] = createSignal<string>("");

    onMount(async () => {
        const response = await fetch("/src/assets/brief.md");

        setHtml(await marked.use({async: true}).parse(await response.text()));

        hljs.highlightAll();
    });

    return <div id="md-content" style={{margin: "auto", "max-width": "800pt"}} innerHTML={html()}/>;
};

const Main = () => (
    <Tabs.Root lazyMount defaultValue="main">
        <Tabs.List>
            <Tabs.Trigger value="main">Main</Tabs.Trigger>
            <Tabs.Trigger value="jackpot">Jackpot</Tabs.Trigger>
            <Tabs.Trigger value="query">Query</Tabs.Trigger>
            <Tabs.Trigger value="process">Process</Tabs.Trigger>
            <Tabs.Trigger value="scripting">Scripting</Tabs.Trigger>
            <Tabs.Trigger value="server">Server</Tabs.Trigger>
            <Tabs.Indicator/>
        </Tabs.List>
        <Tabs.Content value="main"><Brief/></Tabs.Content>
        <Tabs.Content value="jackpot">Hello</Tabs.Content>
        <Tabs.Content value="query">World</Tabs.Content>
        <Tabs.Content value="process"></Tabs.Content>
        <Tabs.Content value="scripting"></Tabs.Content>
        <Tabs.Content value="server"></Tabs.Content>
    </Tabs.Root>
)

export default Main;
