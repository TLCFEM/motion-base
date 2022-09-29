/* @refresh reload */
import {render} from 'solid-js/web';
import './index.css';
import axios from "axios";
import App from './App';

axios.defaults.baseURL = 'http://127.0.0.1:8000';

render(() => <App/>, document.getElementById('header') as HTMLElement);
