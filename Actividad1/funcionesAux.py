import ipaddress

#### Paquete: IP[4 bytes] + PUERTO[2 bytes] + MENSAJE
# Estructura parseada: {"ip": "a.b.c.d", "puerto": int, "mensaje": str}
def parse_packet(IP_packet: bytes) -> dict:
    ip = ".".join(str(b) for b in IP_packet[0:4])
    puerto = int.from_bytes(IP_packet[4:6], byteorder="big")
    mensaje = IP_packet[6:].decode()
    return {"ip": ip, "puerto": puerto, "mensaje": mensaje}


def create_packet(parsed_IP_packet: dict) -> bytes:
    ip_bytes = bytes(int(trozo) for trozo in parsed_IP_packet["ip"].split("."))
    puerto_bytes = parsed_IP_packet["puerto"].to_bytes(2, byteorder="big")
    mensaje_bytes = parsed_IP_packet["mensaje"].encode()
    return ip_bytes + puerto_bytes + mensaje_bytes


def check_routes(routes_file_name: str, destination_address: tuple[str, int]) -> tuple[str, int] | None:
    ip_destino, puerto_destino = destination_address
    ip_destino = ipaddress.ip_address(ip_destino)
    with open(routes_file_name) as archivo:
        for linea in archivo:
            lista_linea = linea.split()
            # ignoramos lineas que no tengan la forma indicada en el enunciado
            if len(lista_linea) != 5:
                continue
            red, puerto_inicial, puerto_final, ip_salto, puerto_salto = lista_linea
            if (ip_destino in ipaddress.ip_network(red, strict=False)
                    and int(puerto_inicial) <= puerto_destino <= int(puerto_final)):
                return (ip_salto, int(puerto_salto))
    return None


if __name__ == "__main__":
    ############ TEST parse y create
    dic = {"ip": "192.168.1.5", "puerto": 8881, "mensaje": "hola"}
    assert dic == parse_packet(create_packet(dic))
    paquete = create_packet(dic)
    assert create_packet(parse_packet(paquete)) == paquete
    print("Tests de parse/create OK")
