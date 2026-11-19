import ipaddress

#### El tamaño del Header es de 20 bytes: IP[4] + PUERTO[2] + TTL[1] + ID[4] + OFFSET[4] + tamaño[4] + FLAG[1]
HEADER_SIZE = 20
# ahora el mensaje se guarda en bytes (no str) porque al fragmentar se puede cortar en medio de un caracter
# Estructura parseada: {"ip": "a.b.c.d", "puerto": int, "ttl": int, "id": int, "offset": int,"tamaño": int, "flag": int, "mensaje": bytes}
def parse_packet(IP_packet):
    ip = ".".join(str(b) for b in IP_packet[0:4])
    puerto = int.from_bytes(IP_packet[4:6], byteorder="big")
    ttl = IP_packet[6]
    id_paquete = int.from_bytes(IP_packet[7:11], byteorder="big")
    offset = int.from_bytes(IP_packet[11:15], byteorder="big")
    tamaño = int.from_bytes(IP_packet[15:19], byteorder="big")
    flag = IP_packet[19]
    mensaje = IP_packet[HEADER_SIZE:]
    return {"ip": ip, "puerto": puerto, "ttl": ttl, "id": id_paquete, "offset": offset,"tamaño": tamaño, "flag": flag, "mensaje": mensaje}


def create_packet(parsed_IP_packet):
    ip_bytes = bytes(int(trozo) for trozo in parsed_IP_packet["ip"].split("."))
    puerto_bytes = parsed_IP_packet["puerto"].to_bytes(2, byteorder="big")
    ttl_bytes = parsed_IP_packet["ttl"].to_bytes(1, byteorder="big")
    id_bytes = parsed_IP_packet["id"].to_bytes(4, byteorder="big")
    offset_bytes = parsed_IP_packet["offset"].to_bytes(4, byteorder="big")


    tamaño_bytes = parsed_IP_packet["tamaño"].to_bytes(4, byteorder="big")
    flag_bytes = parsed_IP_packet["flag"].to_bytes(1, byteorder="big")
    return (ip_bytes + puerto_bytes + ttl_bytes + id_bytes + offset_bytes + tamaño_bytes + flag_bytes + parsed_IP_packet["mensaje"])



# Entrada: routers_file_name: string , destination_address: string,int    , listaRutas: list(red, puerto_inicial, puerto_final, ip_salto, puerto_salto)
# Salida: ((ip_sigueinte_salto, puerto_siguiente_salto), MTU)
def check_routes(routes_file_name, destination_address, listaRutas):
    ip_destino, puerto_destino = destination_address
    ip_destino = ipaddress.ip_address(ip_destino)
    rutasCandidatas = []
    with open(routes_file_name) as archivo:
        for linea in archivo:
            lista_linea = linea.split()
            # ignoramos lineas que no tengan la forma indicada en el enunciado 6 parametros en este caso sumandole MTU
            if len(lista_linea) != 6:
                continue
            red, puerto_inicial, puerto_final, ip_salto, puerto_salto,mtu = lista_linea[:6]
            # Si la ip de destino esta en el intervalo de puerto inicial - puerto final, la agregamos a ruta candidata
            if (ip_destino in ipaddress.ip_network(red, strict=False) and int(puerto_inicial) <= puerto_destino <= int(puerto_final)):
                rutasCandidatas.append((red, int(puerto_inicial), int(puerto_final), ip_salto, int(puerto_salto), int(mtu)))

    # nos quedamos solo con las candidatas de mayor largo de prefijo, de esta manera solo se escogera la ruta default(0.0.0.0), si es la unica
    if rutasCandidatas:
        mayor_prefijo = max(ipaddress.ip_network(r[0], strict=False).prefixlen for r in rutasCandidatas)
        rutasCandidatas = [r for r in rutasCandidatas if ipaddress.ip_network(r[0], strict=False).prefixlen == mayor_prefijo]
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
    return (rutaDefinitiva[3], rutaDefinitiva[4]), rutaDefinitiva[5]

# Fragmenta el paquete en datagramas y retorna lista de datagramas
def fragment_IP_packet(IP_packet, MTU):

    # Si el paquete es más pequeño que MTU, no hay que fragmentar
    if len(IP_packet) <= MTU:
        return [IP_packet]

    # Realizamos parse y fragmentamos
    paquete = parse_packet(IP_packet)
    tamaño_datos_fragmento = MTU - HEADER_SIZE
    mensaje = paquete["mensaje"]
    fragmentos = []
    for inicio in range(0, len(mensaje), tamaño_datos_fragmento):
        # inicio marca el byte en el que debe empezar el fragmento, luego usamos inicio + tamaño_datos_fragmento para indicar el final de los datos del fragmento
        trozo = mensaje[inicio:inicio + tamaño_datos_fragmento]
        # Realizamos copia del diccionario "paquete", para reutilizar los headers en cada fragmento
        fragmento = dict(paquete)
        fragmento["mensaje"] = trozo
        fragmento["tamaño"] = len(trozo)
        fragmento["offset"] = paquete["offset"] + inicio  

        # Como un fragmento se puede fragmentar multiples veces, entonces si ya vamos en el ultimo fragmento reciclamos la flag del padre(el mensaje comienza con la flag en 0)
        if inicio + tamaño_datos_fragmento >= len(mensaje):
            fragmento["flag"] = paquete["flag"] 
        else:
            fragmento["flag"] = 1
        fragmentos.append(create_packet(fragmento))
    return fragmentos

# Re-ensamblar paquete IP
def reassemble_IP_packet(fragment_list):
    # si es lista vacia retornamos none
    if not fragment_list:
        return None
    # creamos un diccionario de la forma {offset:fragmento_parseado}, para asi ordenarlo
    por_offset = {}
    for fragmento in fragment_list:
        parsed = parse_packet(fragmento)
        por_offset[parsed["offset"]] = parsed

    # ordenamos diccionario y definimos fragmentos, el cual es lista de fragmentos ordenados por offset
    fragmentos = [por_offset[offset] for offset in sorted(por_offset)]

    # Ahora revisamos si la lista esta completa, vamos revisando offset por offset, comenzando por offset = 0,

    siguiente_offset = 0
    for fragmento in fragmentos:
        # Si offset != siguiente_offset, se perdio algun fragmento
        if fragmento["offset"] != siguiente_offset:
            return None  
        siguiente_offset += fragmento["tamaño"]
    # Si no hay ningun fragmento faltante entre los fragmentos que tenemos, revisamos que el ultimo sea efectivamente el ultimo
    if fragmentos[-1]["flag"] != 0:
        return None  # falta el ultimo fragmento

    # juntamos los fragmentos de mensajes que tenemos y seteamos todos los headers en paquete
    mensaje = b"".join(f["mensaje"] for f in fragmentos)
    paquete = dict(fragmentos[0])  
    paquete["offset"] = 0
    paquete["tamaño"] = len(mensaje)
    paquete["flag"] = 0
    paquete["mensaje"] = mensaje
    # Retornamos paquete en bytes
    return create_packet(paquete)


if __name__ == "__main__":
    ############ Test parse y create (header completo)
    msg = "hola".encode()
    dic = {"ip": "192.168.1.5", "puerto": 8881, "ttl": 10, "id": 12345, "offset": 0,
           "tamaño": len(msg), "flag": 0, "mensaje": msg}
    assert dic == parse_packet(create_packet(dic))

    ############ Test de reassemble
    mensaje = b"hola" * 30
    IP_packet_v1 = create_packet({"ip": "127.0.0.1", "puerto": 8885, "ttl": 10, "id": 347,"offset": 0, "tamaño": len(mensaje), "flag": 0,"mensaje": mensaje})   
    MTU = 50
    fragment_list = fragment_IP_packet(IP_packet_v1, MTU)
    IP_packet_v2 = reassemble_IP_packet(fragment_list)
    assert IP_packet_v1 == IP_packet_v2
