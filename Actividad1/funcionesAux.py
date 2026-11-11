import ipaddress
#### parser para los mensajes de la forma IP[4bytes];PUERTO[2bytes];MENSAJE
# diccionario de forma {IP:"a.b.c.d",puerto:,mensaje:}
def parse_package(IP_packet:bytes):
    ip_bytes0 = IP_packet[0]
    ip_bytes1 = IP_packet[1]
    ip_bytes2 = IP_packet[2]
    ip_bytes3 = IP_packet[3]    
    ip = f"{ip_bytes0}.{ip_bytes1}.{ip_bytes2}.{ip_bytes3}"
    puerto = int.from_bytes(IP_packet[4:6], byteorder="big")
    mensaje = IP_packet[6:].decode()
    return {"ip": ip, "puerto": puerto, "mensaje": mensaje}

def create_packet(parsed_IP_packet: dict):
    ip = parsed_IP_packet["ip"]
    ip_bytes = b""
    for trozo in ip.split("."):
        ip_bytes += bytes([int(trozo)])
    puerto_bytes = parsed_IP_packet["puerto"].to_bytes(2, byteorder="big")
    mensaje_bytes = parsed_IP_packet["mensaje"].encode()

    return ip_bytes + puerto_bytes + mensaje_bytes
############ TEST parse y create 
dic = {"ip": "192.168.1.5", "puerto": 8881, "mensaje": "hola"}
# test se realiza con assert para no llenar de prints el cmd
assert dic == parse_package(create_packet(dic))
def check_routes(routes_file_name: str, destination_address: tuple[str, int]):
    ip_destino,puerto_destino = destination_address          
    with open(routes_file_name) as archivo:
        for linea in archivo:
            lista_linea = linea.split()
            # ignoramos lineas que no tengan la forma indicada en el enunciado
            if len(lista_linea) != 5:
                continue         
            red, puerto_inicial, puerto_final, ip_salto, puerto_salto = lista_linea
            if (ip_destino in ipaddress.ip_network(red, strict=False) and int(puerto_inicial) <= puerto_destino <= int(puerto_final)):
                return (ip_salto, int(puerto_salto))

