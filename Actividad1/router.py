import sys
import socket
# Recibir IP y puerto desde el .txt
if len(sys.argv) != 4:
    print("Uso: python3 actividad1.py router_IP router_puerto router_rutas.txt")
    sys.exit(1)

router_ip = sys.argv[1]
router_puerto = int(sys.argv[2])  
router_rutas = sys.argv[3]
print(f"Router escuchando en: ({router_ip}, {router_puerto})")
print(f"Tabla de rutas: {router_rutas}")

### Socket No orientaado a conexion que esta escuchando
escuchador = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
escuchador.bind((router_ip,router_puerto))
buffer = 512

while True:
    respuesta, direccion = escuchador.recvfrom(buffer)


#### parser para los mensajes de la forma IP[4bytes];PUERTO[2bytes];MENSAJE
# diccionario de forma {IP:"a.b.c.d",puerto:,mensaje:}
## parsed_IP_packet
def parse_package(IP_packet:bytes):
    pass
def create_packet(parsed_IP_packet: dict):
    pass


