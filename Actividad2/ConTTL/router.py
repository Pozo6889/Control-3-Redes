import sys
import socket
from funcionesAux import parse_packet, create_packet, check_routes

listaRuta = []  # estado del round-robin
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

    # Si el TTL llego a 0, el paquete se descarta (ni se procesa ni se reenvia)
    if paquete["ttl"] <= 0:
        print(f"Se recibió paquete {paquete} con TTL 0")
        continue

    # Caso 1: el paquete es para este router -> imprimimos solo el contenido
    if destino == direccion_router:
        print(paquete["mensaje"].decode())
        continue

    # Caso 2: no es para este router -> buscamos el siguiente salto
    ruta = check_routes(router_rutas, destino, listaRuta)
    if ruta is None:
        print(f"No hay rutas hacia {destino} para paquete {paquete}")
    else:
        next_hop, mtu = ruta  # el MTU aun no se usa (se usara al fragmentar)
        paquete["ttl"] -= 1  # el TTL baja en 1 antes de hacer forward
        print(f"redirigiendo paquete {paquete} con destino final {destino} "
              f"desde {direccion_router} hacia {next_hop}")
        escuchador.sendto(create_packet(paquete), next_hop)
