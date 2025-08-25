import {Tabs} from '@ark-ui/solid/tabs'
import {createSignal, onMount} from "solid-js";
import {marked} from "marked";
import hljs from "highlight.js";

const MarkdownContent = (props: { src: string }) => {
    const [content, setContent] = createSignal<string>("");

    onMount(async () => {
        const response = await fetch(`/src/assets/${props.src}`);

        setContent(
            await marked
                .use({async: true})
                .parse((await response.text()).replace(/\(client_files\//g, "(/src/assets/client_files/")),
        );

        hljs.highlightAll();
    });

    return <div style={{margin: "auto", "max-width": "800pt"}} innerHTML={content()}/>;
};

const Main = () => (
    <Tabs.Root defaultValue="main" lazyMount>
        <Tabs.List>
            <Tabs.Trigger value="main">Main</Tabs.Trigger>
            <Tabs.Trigger value="jackpot">Jackpot</Tabs.Trigger>
            <Tabs.Trigger value="query">Query</Tabs.Trigger>
            <Tabs.Trigger value="process">Process</Tabs.Trigger>
            <Tabs.Trigger value="scripting">Scripting</Tabs.Trigger>
            <Tabs.Trigger value="server">Server</Tabs.Trigger>
        </Tabs.List>
        <Tabs.Content value="main"><MarkdownContent src="brief.md"/></Tabs.Content>
        <Tabs.Content value="jackpot">Hello</Tabs.Content>
        <Tabs.Content value="query">World</Tabs.Content>
        <Tabs.Content value="process"></Tabs.Content>
        <Tabs.Content value="scripting"><MarkdownContent src="client.md"/></Tabs.Content>
        <Tabs.Content value="server"></Tabs.Content>
    </Tabs.Root>
)

export default Main;
