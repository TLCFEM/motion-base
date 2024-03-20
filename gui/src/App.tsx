import { Component, createSignal } from 'solid-js'
import { jackpot, SeismicRecord } from './API'
import { Card, CardContent, Typography } from '@suid/material'


const App: Component = () => {
  let [data, setData] = createSignal<SeismicRecord>({} as SeismicRecord)

  jackpot().then(r => setData(r))

  return <Card sx={{ minWidth: 275 }}>
    <CardContent>
      <Typography variant="h6" color="text.secondary">
        ID
      </Typography>
      <Typography variant="body1">
        {data().id}
      </Typography>
      <Typography variant="h6" color="text.secondary">
        Magnitude
      </Typography>
      <Typography variant="body1">
        {data().magnitude}
      </Typography>
      <Typography variant="body1">
        {data().file_name}
      </Typography>
    </CardContent>
  </Card>
}

export default App
