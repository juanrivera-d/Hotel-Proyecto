from locust import HttpUser, task, between

class HotelUser(HttpUser):
    wait_time = between(1, 2)

    @task(3)
    def consultar_habitaciones(self):
        self.client.get("/api/habitaciones")

    @task(2)
    def consultar_servicios(self):
        self.client.get("/api/servicios")

    @task(1)
    def consultar_analitica(self):
        self.client.get("/api/analytics/trafico-logs")
