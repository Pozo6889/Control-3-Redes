import ipaddress

#### Paquete: IP[4 bytes] + PUERTO[2 bytes] + TTL[1 byte] + MENSAJE
# Estructura parseada: {"ip": "a.b.c.d", "puerto": int, "ttl": int, "mensaje": str}
def parse_packet(IP_packet: bytes):
    ip = ".".join(str(b) for b in IP_packet[0:4])
    puerto = int.from_bytes(IP_packet[4:6], byteorder="big")
    ttl = IP_packet[6]
    mensaje = IP_packet[7:].decode()
    return {"ip": ip, "puerto": puerto, "ttl": ttl, "mensaje": mensaje}


def create_packet(parsed_IP_packet: dict):
    ip_bytes = bytes(int(trozo) for trozo in parsed_IP_packet["ip"].split("."))
    puerto_bytes = parsed_IP_packet["puerto"].to_bytes(2, byteorder="big")
    ttl_bytes = parsed_IP_packet["ttl"].to_bytes(1, byteorder="big")
    mensaje_bytes = parsed_IP_packet["mensaje"].encode()
    return ip_bytes + puerto_bytes + ttl_bytes + mensaje_bytes

# routers_file_name: string , destination_address: string,int    , listaRutas: list(red, puerto_inicial, puerto_final, ip_salto, puerto_salto)
def check_routes(routes_file_name, destination_address, listaRutas):
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
    #Chequeamos entre las rutas candidatas, las que no se han utilizado en esta iteracion
    rutasCandidatasNoUsadas = []
    for ruta in rutasCandidatas:
        if ruta not in listaRutas:
            rutasCandidatasNoUsadas.append(ruta)
    rutaDefinitiva = None
    #Si todas las rutas han sido usadas, entonces las quitamos de la lista global (para habilitar su uso)
    if not rutasCandidatasNoUsadas:
        for ruta in rutasCandidatas:
            listaRutas.remove(ruta)
        rutasCandidatasNoUsadas = rutasCandidatas
    #Guardamos la primera ruta no Usada y la quitamos de la lista global (para que no se repita su uso en esta iteracion)
    rutaDefinitiva = rutasCandidatasNoUsadas[0]
    listaRutas.append(rutaDefinitiva)
    return (rutaDefinitiva[3], rutaDefinitiva[4])


if __name__ == "__main__":
    ############ TEST parse y create (con TTL)
    dic = {"ip": "192.168.1.5", "puerto": 8881, "ttl": 10, "mensaje": "hola"}
    assert dic == parse_packet(create_packet(dic))
    paquete = create_packet(dic)
    assert create_packet(parse_packet(paquete)) == paquete
    # paquete armado a mano: 127.0.0.1 | 8883 (0x22B3) | TTL 1 | "hola"
    manual = bytes([127, 0, 0, 1, 0x22, 0xB3, 1]) + b"hola"
    print("IP_packet_v1 == IP_packet_v2 ? {}".format(manual == create_packet(parse_packet(manual))))
