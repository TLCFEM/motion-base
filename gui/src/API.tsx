import axios from 'axios'

axios.defaults.baseURL = 'http://127.0.0.1:8000'

export class SeismicRecord {
  public endpoint: string = ''

  public id: string = ''
  public file_name: string = ''
  public category: string = ''
  public region: string = ''
  public uploaded_by: string = ''

  public magnitude: number = 0
  public maximum_acceleration: number = 0

  public event_time: string = ''
  public event_location: Array<number> = Array<number>(0)
  public depth: number = 0

  public station_code: string = ''
  public station_location: Array<number> = Array<number>(0)
  public station_elevation: number = 0
  public station_elevation_unit: string = ''
  public record_time: string = ''

  public sampling_frequency: number = 0
  public sampling_frequency_unit: string = ''
  public duration: number = 0
  public direction: string = ''
  public scale_factor: number = 0


  public time_interval: number = 0
  public waveform: Array<number> = Array<number>(0)

  public frequency_interval: number = 0
  public spectrum: Array<number> = Array<number>(0)

  public period: Array<number> = Array<number>(0)
  public displacement_spectrum: Array<number> = Array<number>(0)
  public velocity_spectrum: Array<number> = Array<number>(0)
  public acceleration_spectrum: Array<number> = Array<number>(0)

  public constructor(data: any) {
    Object.assign(this, data)
  }
}

export async function jackpot() {
  return (await axios.get<SeismicRecord>('/waveform/jackpot')).data
}

