import ipaddress

#### Header (20 bytes): IP[4] + PUERTO[2] + TTL[1] + ID[4] + OFFSET[4] + TAMANO[4] + FLAG[1], luego el MENSAJE
# Estructura parseada:
# {"ip": "a.b.c.d", "puerto": int, "ttl": int, "id": int, "offset": int,
#  "tamano": int, "flag": int, "mensaje": bytes}
# El mensaje se guarda como bytes (no str) porque al fragmentar se puede cortar en medio de un caracter.
HEADER_SIZE = 20


def parse_packet(IP_packet: bytes) -> dict:
    ip = ".".join(str(b) for b in IP_packet[0:4])
    puerto = int.from_bytes(IP_packet[4:6], byteorder="big")
    ttl = IP_packet[6]
    id_paquete = int.from_bytes(IP_packet[7:11], byteorder="big")
    offset = int.from_bytes(IP_packet[11:15], byteorder="big")
    tamano = int.from_bytes(IP_packet[15:19], byteorder="big")
    flag = IP_packet[19]
    mensaje = IP_packet[HEADER_SIZE:]
    return {"ip": ip, "puerto": puerto, "ttl": ttl, "id": id_paquete, "offset": offset,
            "tamano": tamano, "flag": flag, "mensaje": mensaje}


def create_packet(parsed_IP_packet: dict) -> bytes:
    ip_bytes = bytes(int(trozo) for trozo in parsed_IP_packet["ip"].split("."))
    puerto_bytes = parsed_IP_packet["puerto"].to_bytes(2, byteorder="big")
    ttl_bytes = parsed_IP_packet["ttl"].to_bytes(1, byteorder="big")
    id_bytes = parsed_IP_packet["id"].to_bytes(4, byteorder="big")
    offset_bytes = parsed_IP_packet["offset"].to_bytes(4, byteorder="big")
    tamano_bytes = parsed_IP_packet["tamano"].to_bytes(4, byteorder="big")
    flag_bytes = parsed_IP_packet["flag"].to_bytes(1, byteorder="big")
    return (ip_bytes + puerto_bytes + ttl_bytes + id_bytes + offset_bytes
            + tamano_bytes + flag_bytes + parsed_IP_packet["mensaje"])


MTU_POR_DEFECTO = 1500  # para lineas de tablas antiguas, sin columna de MTU


def check_routes(routes_file_name: str, destination_address: tuple[str, int], listaRutas):
    """Retorna ((next_hop_ip, next_hop_puerto), MTU) o None si no hay ruta."""
    ip_destino, puerto_destino = destination_address
    ip_destino = ipaddress.ip_address(ip_destino)
    rutasCandidatas = []
    with open(routes_file_name) as archivo:
        for linea in archivo:
            lista_linea = linea.split()
            # formato: red puerto_inicial puerto_final ip_salto puerto_salto [MTU]
            # ignoramos lineas que no tengan 5 o 6 campos
            if len(lista_linea) not in (5, 6):
                continue
            red, puerto_inicial, puerto_final, ip_salto, puerto_salto = lista_linea[:5]
            mtu = int(lista_linea[5]) if len(lista_linea) == 6 else MTU_POR_DEFECTO
            if (ip_destino in ipaddress.ip_network(red, strict=False)
                    and int(puerto_inicial) <= puerto_destino <= int(puerto_final)):
                rutasCandidatas.append((red, int(puerto_inicial), int(puerto_final), ip_salto, int(puerto_salto), mtu))
    # La ruta default (0.0.0.0/0) solo debe usarse si no hay otra ruta mas especifica:
    # nos quedamos solo con las candidatas de mayor largo de prefijo.
    if rutasCandidatas:
        mayor_prefijo = max(ipaddress.ip_network(r[0], strict=False).prefixlen for r in rutasCandidatas)
        rutasCandidatas = [r for r in rutasCandidatas
                           if ipaddress.ip_network(r[0], strict=False).prefixlen == mayor_prefijo]
    # Si no hay ninguna ruta, retornamos None
    if not rutasCandidatas:
        return None
    # Round-robin: rutas candidatas que no se han usado en esta vuelta
    rutasCandidatasNoUsadas = [ruta for ruta in rutasCandidatas if ruta not in listaRutas]
    # Si todas fueron usadas, las liberamos para comenzar una nueva vuelta
    if not rutasCandidatasNoUsadas:
        for ruta in rutasCandidatas:
            listaRutas.remove(ruta)
        rutasCandidatasNoUsadas = rutasCandidatas
    # Usamos la primera no usada y la marcamos como usada
    rutaDefinitiva = rutasCandidatasNoUsadas[0]
    listaRutas.append(rutaDefinitiva)
    return (rutaDefinitiva[3], rutaDefinitiva[4]), rutaDefinitiva[5]


def fragment_IP_packet(IP_packet: bytes, MTU: int) -> list[bytes]:
    """Fragmenta IP_packet (header + datos, en bytes) para que cada fragmento mida a lo mas MTU bytes.
    Retorna una lista con al menos un elemento. Sirve tambien para re-fragmentar un fragmento."""
    # Caso 1: el paquete cabe por el enlace, no se fragmenta
    if len(IP_packet) <= MTU:
        return [IP_packet]
    if MTU <= HEADER_SIZE:
        raise ValueError(f"MTU {MTU} demasiado pequeno: el header ya mide {HEADER_SIZE} bytes")

    # Caso 2: hay que fragmentar. Cada trozo de mensaje mide MTU - HEADER_SIZE bytes
    paquete = parse_packet(IP_packet)
    datos_por_fragmento = MTU - HEADER_SIZE
    mensaje = paquete["mensaje"]
    fragmentos = []
    for inicio in range(0, len(mensaje), datos_por_fragmento):
        trozo = mensaje[inicio:inicio + datos_por_fragmento]
        fragmento = dict(paquete)  # copia: mantiene ip, puerto, ttl e id
        fragmento["mensaje"] = trozo
        fragmento["tamano"] = len(trozo)
        fragmento["offset"] = paquete["offset"] + inicio  # relativo al datagrama original
        es_ultimo = inicio + datos_por_fragmento >= len(mensaje)
        # Todos llevan FLAG 1 salvo el ultimo, que hereda el FLAG del paquete recibido
        # (si el paquete ya era un fragmento no final, su ultimo trozo tambien debe llevar 1)
        fragmento["flag"] = paquete["flag"] if es_ultimo else 1
        fragmentos.append(create_packet(fragmento))
    return fragmentos


def reassemble_IP_packet(fragment_list: list[bytes]) -> bytes | None:
    """Re-ensambla un paquete IP a partir de una lista de fragmentos (en bytes, en cualquier orden).
    Retorna el paquete completo en bytes, o None si aun faltan fragmentos."""
    if not fragment_list:
        return None
    # Ordenamos por offset; si un mismo offset llega repetido nos quedamos con una sola copia
    por_offset = {}
    for fragmento in fragment_list:
        parsed = parse_packet(fragmento)
        por_offset[parsed["offset"]] = parsed
    fragmentos = [por_offset[offset] for offset in sorted(por_offset)]

    # La lista esta completa si: parte en offset 0, cada fragmento empieza donde termina el anterior
    # y el ultimo tiene FLAG 0. (Un paquete sin fragmentar cumple esto con un solo elemento.)
    siguiente_offset = 0
    for fragmento in fragmentos:
        if fragmento["offset"] != siguiente_offset:
            return None  # falta algun fragmento
        siguiente_offset += fragmento["tamano"]
    if fragmentos[-1]["flag"] != 0:
        return None  # falta el ultimo fragmento

    mensaje = b"".join(f["mensaje"] for f in fragmentos)
    paquete = dict(fragmentos[0])  # IP, puerto, TTL e ID: los del primer fragmento
    paquete["offset"] = 0
    paquete["tamano"] = len(mensaje)
    paquete["flag"] = 0
    paquete["mensaje"] = mensaje
    return create_packet(paquete)


if __name__ == "__main__":
    ############ TEST parse y create (header completo)
    msg = "hola, ñandú".encode()
    dic = {"ip": "192.168.1.5", "puerto": 8881, "ttl": 10, "id": 12345, "offset": 0,
           "tamano": len(msg), "flag": 0, "mensaje": msg}
    assert dic == parse_packet(create_packet(dic))
    # paquete armado a mano: 127.0.0.1 | 8883 | TTL 1 | ID 7 | offset 0 | tamano 4 | flag 0 | "hola"
    manual = (bytes([127, 0, 0, 1, 0x22, 0xB3, 1]) + (7).to_bytes(4, "big") + (0).to_bytes(4, "big")
              + (4).to_bytes(4, "big") + bytes([0]) + b"hola")
    print("IP_packet_v1 == IP_packet_v2 ? {}".format(manual == create_packet(parse_packet(manual))))


    ############ TEST fragment_IP_packet
    def paquete_de_prueba(largo_mensaje, id_paquete=347):
        m = bytes(i % 256 for i in range(largo_mensaje))
        return create_packet({"ip": "127.0.0.1", "puerto": 8885, "ttl": 10, "id": id_paquete,
                              "offset": 0, "tamano": len(m), "flag": 0, "mensaje": m})

    def unir(fragmentos):  # reconstruye el mensaje solo para verificar (no es reassemble_IP_packet)
        partes = sorted((parse_packet(f) for f in fragmentos), key=lambda p: p["offset"])
        return b"".join(p["mensaje"] for p in partes)

    original = paquete_de_prueba(130)  # 150 bytes en total
    # a) cabe por el enlace -> lista de tamano 1 con el mismo paquete
    assert fragment_IP_packet(original, 150) == [original]
    assert fragment_IP_packet(original, 200) == [original]
    # b) MTU 100 -> 2 fragmentos (80 + 50 bytes de datos); MTU 50 -> 5 fragmentos (30*4 + 10)
    for mtu, esperado in [(100, 2), (50, 5)]:
        frags = fragment_IP_packet(original, mtu)
        info = [(p["offset"], p["tamano"], p["flag"]) for p in map(parse_packet, frags)]
        print(f"MTU {mtu}: {len(frags)} fragmentos, largos {[len(f) for f in frags]}, (offset, tamano, flag) = {info}")
        assert len(frags) == esperado
        assert all(len(f) <= mtu for f in frags)
        assert unir(frags) == parse_packet(original)["mensaje"]
    # c) re-fragmentar un fragmento: el ultimo hereda el FLAG del fragmento recibido
    primero, segundo = fragment_IP_packet(original, 100)       # flags 1 y 0
    sub_p = [parse_packet(f) for f in fragment_IP_packet(primero, 50)]
    sub_s = [parse_packet(f) for f in fragment_IP_packet(segundo, 50)]
    assert [(p["offset"], p["tamano"], p["flag"]) for p in sub_p] == [(0, 30, 1), (30, 30, 1), (60, 20, 1)]
    assert [(p["offset"], p["tamano"], p["flag"]) for p in sub_s] == [(80, 30, 1), (110, 20, 0)]
    print("Tests de fragment_IP_packet OK")


    ############ TEST reassemble_IP_packet
    import random as _random
    IP_packet_v1 = paquete_de_prueba(130)
    for mtu in (200, 150, 100, 50, 30, 21):
        fragment_list = fragment_IP_packet(IP_packet_v1, mtu)
        IP_packet_v2 = reassemble_IP_packet(fragment_list)
        print("MTU {}: {} fragmentos, IP_packet_v1 == IP_packet_v2 ? {}".format(mtu, len(fragment_list), IP_packet_v1 == IP_packet_v2))
        assert IP_packet_v1 == IP_packet_v2
        # en desorden (varias permutaciones)
        for _ in range(20):
            _random.shuffle(fragment_list)
            assert reassemble_IP_packet(fragment_list) == IP_packet_v1
    frags = fragment_IP_packet(IP_packet_v1, 50)  # 5 fragmentos
    # listas incompletas -> None
    assert reassemble_IP_packet([]) is None
    assert reassemble_IP_packet(frags[1:]) is None              # falta el primero
    assert reassemble_IP_packet(frags[:-1]) is None             # falta el ultimo
    assert reassemble_IP_packet(frags[:2] + frags[3:]) is None  # falta uno del medio
    assert reassemble_IP_packet([frags[0]]) is None             # un solo fragmento (no final)
    assert reassemble_IP_packet([frags[-1]]) is None            # un solo fragmento (final, offset > 0)
    # un paquete sin fragmentar (lista de tamano 1) se devuelve completo
    assert reassemble_IP_packet([IP_packet_v1]) == IP_packet_v1
    # fragmentos repetidos no molestan
    assert reassemble_IP_packet(frags + frags[:2]) == IP_packet_v1
    # mezcla de fragmentos re-fragmentados (como ocurre con MTUs distintos en la ruta)
    grandes = fragment_IP_packet(IP_packet_v1, 100)
    mezcla = fragment_IP_packet(grandes[0], 50) + [grandes[1]]
    assert reassemble_IP_packet(mezcla[::-1]) == IP_packet_v1
    print("Tests de reassemble_IP_packet OK")

