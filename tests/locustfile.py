from locust import task, FastHttpUser


class HelloWorldUser(FastHttpUser):
    @task
    def raw(self):
        self.client.get("/raw/jackpot")

    @task
    def waveform(self):
        self.client.get("/waveform/jackpot")
