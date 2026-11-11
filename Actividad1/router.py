import sys
import socket
# Recibir IP y puerto desde el .txt
if len(sys.argv) != 4:
    print("Uso: python3 actividad1.py router_IP router_puerto router_rutas.txt")
    sys.exit(1)

router_ip = sys.argv[1]
router_puerto = int(sys.argv[2])  
router_rutas = sys.argv[3]
print(f"Router escuchando en: ({router_ip}, {router_puerto})")
print(f"Tabla de rutas: {router_rutas}")

#### parser para los mensajes de la forma IP[4bytes];PUERTO[2bytes];MENSAJE
# diccionario de forma {IP:"a.b.c.d",puerto:,mensaje:}
## parsed_IP_packet
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



### Socket No orientaado a conexion que esta escuchando
escuchador = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
escuchador.bind((router_ip,router_puerto))
buffer = 512

while True:
    respuesta, direccion = escuchador.recvfrom(buffer)





