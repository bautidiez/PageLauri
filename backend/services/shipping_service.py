class ShippingService:
    @staticmethod
    def calculate_cost(zip_code):
        """
        Lógica para calcular costos de envío basados en el CP. 
        En un entorno real, aquí llamaríamos a la API de Andreani o Correo Argentino.
        """
        zip_code_val = int(zip_code)
        
        # Simulación de costos
        options = [
            {
                "id": "correo_argentino",
                "nombre": "Correo Argentino (Sucursal)",
                "costo": 3500 if zip_code_val < 2000 else 4800,
                "tiempo_estimado": "3 a 5 días hábiles"
            },
            {
                "id": "andreani_domicilio",
                "nombre": "Andreani Premium (Domicilio)",
                "costo": 5200 if zip_code_val < 2000 else 7500,
                "tiempo_estimado": "2 a 3 días hábiles"
            },
            {
                "id": "retiro_local",
                "nombre": "Retiro en Local (Gratis)",
                "costo": 0,
                "tiempo_estimado": "Inmediato - Te avisaremos por WhatsApp"
            }
        ]
        
        return options
