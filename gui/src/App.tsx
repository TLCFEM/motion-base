import 'tippy.js/dist/tippy.css'
import 'tippy.js/themes/translucent.css'
import 'tippy.js/animations/scale.css'
import 'leaflet/dist/leaflet.css'
// @ts-ignore
import * as ST from '@suid/types'
import AppBar from '@suid/material/AppBar'
import Box from '@suid/material/Box'
import Button from '@suid/material/Button'
// @ts-ignore
import L from 'leaflet'
import Link from "@suid/material/Link"
import LoginIcon from '@suid/icons-material/Login'
import Modal from "@suid/material/Modal"
import Paper from "@suid/material/Paper"
// @ts-ignore
import Plotly from 'plotly.js-dist-min'
import Stack from "@suid/material/Stack"
import tippy from 'tippy.js'
import Toolbar from '@suid/material/Toolbar'
import type {Component} from 'solid-js'
import {createSignal, onMount} from 'solid-js'
import Typography from '@suid/material/Typography'
import logo from './assets/logo.svg'
import mongodb from './assets/mongodb.svg'
import fastapi from './assets/fastapi.svg'
import beanie from './assets/beanie.svg'
import solid from './assets/solid.svg'
import tippylogo from './assets/tippy.svg'
import plotlylogo from './assets/plotly.svg'
import leaflletlogo from './assets/leaflet.svg'
import Jackpot from "./Jackpot"
import Container from "@suid/material/Container"
import {Navigate, Route, Routes} from '@solidjs/router'
import ProcessPage from "./Process"
import SearchPage from "./Search"
import axios from "axios";

const [open_about, set_open_about] = createSignal(false);

const AboutModal = () => {
    const about_toggle_off = () => set_open_about(false);

    return <Modal
        component='div' open={open_about()} onClose={about_toggle_off} aria-labelledby="about-model"
        aria-describedby="about-model">
        <Box component={Paper} sx={{
            position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", p: 2,
        }}>
            <Stack direction="row" spacing={2} sx={{p: 1}} alignItems='center'>
                <img src={logo} alt='logo' height='50px'/>
                <Typography variant="h4" sx={{p: 1}}>
                    About
                </Typography>
            </Stack>
            <Typography variant="body1" sx={{p: 1}}>
                This is a demo of strong motion database. The source code is available at GitHub.
            </Typography>
            <Typography variant="h6" sx={{p: 1}}>
                Japan Database
            </Typography>
            <Typography variant="body1" sx={{p: 1}}>
                The data is retrieved from <Link
                href="https://www.kyoshin.bosai.go.jp/kyoshin/data/index_en.html">NIED</Link>. The data is not
                processed. Users may want to further filter the records.
            </Typography>
            <Typography variant="h6" sx={{p: 1}}>
                New Zealand Database
            </Typography>
            <Typography variant="body1" sx={{p: 1}}>
                The data is retrieved from <Link
                href="https://www.geonet.org.nz/data/supplementary/nzsmdb">New Zealand
                Strong-Motion</Link> database. The selected strong motions are processed (*.V2A files). The other
                records (*.V1A files) are not processed. Users may want to further filter the records.
            </Typography>
            <Typography variant="h6" sx={{p: 1}}>
                Built with
            </Typography>
            <Stack direction="row" spacing={3} sx={{p: 1}} alignItems='center' justifyContent='center'>
                <img src={mongodb} alt='mongodb' height='40px'/>
                <img src={fastapi} alt='fastapi' height='40px'/>
                <img src={solid} alt='solid' height='40px'/>
            </Stack>
            <Stack direction="row" spacing={3} sx={{p: 1}} alignItems='center' justifyContent='center'>
                <img src={beanie} alt='beanie' height='40px'/>
                <img src={leaflletlogo} alt='leaflet' height='40px'/>
                <img src={plotlylogo} alt='plotly' height='40px'/>
                <img src={tippylogo} alt='tippy' height='40px'/>
            </Stack>
        </Box>
    </Modal>
}

const login = () => {
}

const ButtonStack: Component = () => {
    const about_toggle_on = () => set_open_about(true);

    onMount(() => {
        tippy('#login', {
            arrow: true, animation: 'scale', inertia: true, theme: 'translucent', content: 'Login to Upload!',
        })
    })

    return <Stack spacing={2} direction="row" alignItems={'center'}>
        <Link href='/jackpot'><Button variant='contained' id='jackpot'>Jackpot</Button></Link>
        <Link href='/search'><Button variant='contained' id='search'>Search</Button></Link>
        <Link href='/process'><Button variant='contained' id='process'>Process</Button></Link>
        <Link href={`${axios.defaults.baseURL}/docs`}><Button variant='contained' id='api'>API</Button></Link>
        <Button variant='contained' id='about' onClick={about_toggle_on}>About</Button>
        <Button variant='contained' id='login' onClick={login}><LoginIcon/></Button>
    </Stack>
}

const App: Component = () => {
    return <Container maxWidth={false}>
        <AppBar position='static' id='app-bar' sx={{mb: 2}}><Toolbar>
            <Typography variant='h5' sx={{flexGrow: 2}}>
                Motion Base
            </Typography>
            <ButtonStack/>
        </Toolbar></AppBar>
        <Box>
            <Routes>
                <Route path='/' element={<Navigate href={({navigate, location}) => '/jackpot'}/>}/>
                <Route path='/jackpot' component={Jackpot}/>
                <Route path='/search' component={SearchPage}/>
                <Route path='/process' component={ProcessPage}/>
            </Routes>
        </Box>
        <AboutModal/>
    </Container>
}

export default App
