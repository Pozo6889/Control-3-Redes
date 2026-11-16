import sys
import socket
import random
from funcionesAux import create_packet

# Uso: python prueba_router.py "IP;puerto;TTL" IP_router_inicial puerto_router_inicial [archivo]
# Ejemplo: python prueba_router.py "127.0.0.1;8885;10" 127.0.0.1 8881
# (las comillas son necesarias porque ';' separa comandos en varias terminales)
if len(sys.argv) not in (4, 5):
    print('Uso: python prueba_router.py "IP;puerto;TTL" IP_router_inicial puerto_router_inicial [archivo]')
    sys.exit(1)

ip_final, puerto_final, ttl = sys.argv[1].split(";")
router_inicial = (sys.argv[2], int(sys.argv[3]))
nombre_archivo = sys.argv[4] if len(sys.argv) == 5 else "mensajes.txt"

enviador = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
with open(nombre_archivo, encoding="utf-8") as archivo:
    for linea in archivo:
        linea = linea.rstrip("\r\n")
        mensaje_bytes = linea.encode()
        paquete = {"ip": ip_final, "puerto": int(puerto_final), "ttl": int(ttl),
                   "id": random.randint(0, 2**32 - 1), "offset": 0,
                   "tamano": len(mensaje_bytes), "flag": 0, "mensaje": mensaje_bytes}
        enviador.sendto(create_packet(paquete), router_inicial)
enviador.close()
