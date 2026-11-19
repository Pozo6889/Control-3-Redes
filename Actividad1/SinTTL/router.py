import sys
import socket
from funcionesAux import parse_packet, create_packet, check_routes

listaRuta = []
# Recibimos parametros del router
if len(sys.argv) != 4:
    print("Uso: python3 router.py router_IP router_puerto router_rutas.txt")
    sys.exit(1)

router_ip = sys.argv[1]
router_puerto = int(sys.argv[2])
router_rutas = sys.argv[3]
direccion_router = (router_ip, router_puerto)
print(f"Router escuchando en: {direccion_router}")
print(f"Tabla de rutas: {router_rutas}")

# Socket no orientado a conexion, escucha bloqueante
escuchador = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
escuchador.bind(direccion_router)
buffer = 512

while True:
    paquete_bytes, direccion = escuchador.recvfrom(buffer)
    paquete = parse_packet(paquete_bytes)
    destino = (paquete["ip"], paquete["puerto"])

    # Caso 1: el paquete es para este router hacemos print
    if destino == direccion_router:
        print(paquete["mensaje"])
        continue

    # Caso 2: no es para este router, checkeamos rutas para enviar paquete
    next_hop = check_routes(router_rutas, destino,listaRuta)
    if next_hop is None:
        print(f"No hay rutas hacia {destino} para paquete {paquete}")
    else:
        print(f'Redirigiendo mensaje "{paquete["mensaje"]}", recibido desde {direccion[1]} estando ahora en {router_puerto}, enviando a {next_hop[1]} con destino final {destino}')
        escuchador.sendto(create_packet(paquete), next_hop)