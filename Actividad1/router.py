
import sys
import socket
from funcionesAux import parse_packet, create_packet, check_routes
 
if len(sys.argv) != 4:
    print("Uso: python3 router.py router_IP router_puerto router_rutas.txt")
    sys.exit(1)
 
router_ip = sys.argv[1]
router_puerto = int(sys.argv[2])
router_rutas = sys.argv[3]
print(f"Router escuchando en: ({router_ip}, {router_puerto})")
print(f"Tabla de rutas: {router_rutas}")
 
### Socket no orientado a conexion, escucha bloqueante
escuchador = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
escuchador.bind((router_ip, router_puerto))
buffer = 512
 
while True:
    paquete_bytes, direccion = escuchador.recvfrom(buffer)
    paquete = parse_packet(paquete_bytes)
    print(f"Recibido: {paquete}")
    # TODO Parte I: forwarding, round-robin