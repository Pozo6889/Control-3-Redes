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


def check_routes(routes_file_name: str, destination_address: tuple[str, int], listaRutas) -> tuple[str, int] | None:
    ip_destino, puerto_destino = destination_address
    ip_destino = ipaddress.ip_address(ip_destino)
    rutasCandidatas = []
    with open(routes_file_name) as archivo:
        for linea in archivo:
            lista_linea = linea.split()
            # ignoramos lineas que no tengan la forma indicada en el enunciado
            if len(lista_linea) != 5:
                continue
            red, puerto_inicial, puerto_final, ip_salto, puerto_salto = lista_linea
            if (ip_destino in ipaddress.ip_network(red, strict=False)
                    and int(puerto_inicial) <= puerto_destino <= int(puerto_final)):
                rutasCandidatas.append((red, int(puerto_inicial), int(puerto_final), ip_salto, int(puerto_salto)))
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
    return (rutaDefinitiva[3], rutaDefinitiva[4])


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
