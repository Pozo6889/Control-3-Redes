import sys
import socket
from funcionesAux import parse_packet, create_packet, check_routes

if len(sys.argv) != 4:
    print("Uso: python3 router.py router_IP router_puerto router_rutas.txt")
    sys.exit(1)

router_ip = sys.argv[1]
router_puerto = int(sys.argv[2])
router_rutas = sys.argv[3]
direccion_router = (router_ip, router_puerto)
print(f"Router escuchando en: {direccion_router}")
print(f"Tabla de rutas: {router_rutas}")

### Socket no orientado a conexion, escucha bloqueante
escuchador = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
escuchador.bind(direccion_router)
buffer = 512

while True:
    paquete_bytes, direccion = escuchador.recvfrom(buffer)
    paquete = parse_packet(paquete_bytes)
    destino = (paquete["ip"], paquete["puerto"])
    direccion_router = (router_ip, router_puerto)

    # Caso 1: el paquete es para este router -> imprimimos solo el contenido
    if destino == direccion_router:
        print(paquete["mensaje"])
        continue

    # Caso 2: no es para este router -> buscamos el siguiente salto
    next_hop = check_routes(router_rutas, destino)
    if next_hop is None:
        print(f"No hay rutas hacia {destino} para paquete {paquete_bytes}")
    else:
        print(f"redirigiendo paquete {paquete_bytes} con destino final {destino} "
              f"desde {direccion_router} hacia {next_hop}")
        escuchador.sendto(create_packet(paquete), next_hop)