import { defineConfig } from "vite";
import solidPlugin from "vite-plugin-solid";
// import devtools from 'solid-devtools/vite';

export default defineConfig({
    plugins: [
        /* 
        Uncomment the following line to enable solid-devtools.
        For more info see https://github.com/thetarnav/solid-devtools/tree/main/packages/extension#readme
        */
        // devtools(),
        solidPlugin(),
    ],
    server: {
        port: 3000,
        // https: {
        //     key: '/cert/private.key',
        //     cert: '/cert/certificate.crt',
        //     ca: '/cert/ca_bundle.crt',
        // }
    },
    build: {
        target: "esnext",
        chunkSizeWarningLimit: 5000,
    },
    base: "./",
});
