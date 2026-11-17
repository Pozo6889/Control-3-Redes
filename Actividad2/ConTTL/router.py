import sys
import socket
from funcionesAux import parse_packet, create_packet, check_routes, fragment_IP_packet, reassemble_IP_packet, fragment_IP_packet

listaRuta = []  # estado del round-robin
fragmentos_por_id = {}  # ID -> lista de fragmentos/paquetes (en bytes) recibidos para ese ID
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

    # Caso 1: el paquete (o fragmento) es para este router -> lo guardamos segun su ID
    # e intentamos re-ensamblar el datagrama con todo lo recibido para ese ID
    if destino == direccion_router:
        id_paquete = paquete["id"]
        fragmentos_por_id.setdefault(id_paquete, []).append(paquete_bytes)
        completo = reassemble_IP_packet(fragmentos_por_id[id_paquete])
        if completo is not None:
            print(parse_packet(completo)["mensaje"].decode(errors="replace"))
            del fragmentos_por_id[id_paquete]  # ya se entrego: liberamos esa entrada
        # si retorna None aun faltan fragmentos: seguimos esperando
        continue

    # Caso 2: no es para este router -> buscamos el siguiente salto
    ruta = check_routes(router_rutas, destino, listaRuta)
    if ruta is None:
        print(f"No hay rutas hacia {destino} para paquete {paquete}")
    else:
        next_hop, mtu = ruta
        paquete["ttl"] -= 1  # el TTL baja en 1 antes de hacer forward
        print(f"redirigiendo paquete {paquete} con destino final {destino} "
              f"desde {direccion_router} hacia {next_hop}")
        # Fragmentamos segun el MTU del enlace y enviamos cada fragmento al siguiente salto
        fragmentos = fragment_IP_packet(create_packet(paquete), mtu)
        if len(fragmentos) > 1:
            print(f"  fragmentando en {len(fragmentos)} fragmentos (MTU {mtu})")
        for fragmento in fragmentos:
            escuchador.sendto(fragmento, next_hop)