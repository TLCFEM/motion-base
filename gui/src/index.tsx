import {render} from 'solid-js/web'
import './index.css'
import axios from "axios"
import App from './App'
import {Router} from '@solidjs/router'

axios.defaults.baseURL = 'http://127.0.0.1:8000'

render(() => <Router><App/></Router>, document.getElementById('root') as HTMLElement)
