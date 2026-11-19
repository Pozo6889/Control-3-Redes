import sys
import socket
from funcionesAux import create_packet
# el último parametro es el nombre del archivo
# Uso: python prueba_router.py "IP;puerto;TTL" IP_router_inicial puerto_router_inicial [archivo]
if len(sys.argv) not in (4, 5):
    print('Uso: python prueba_router.py "IP;puerto;TTL" IP_router_inicial puerto_router_inicial [archivo]')
    sys.exit(1)

ip_final, puerto_final, ttl = sys.argv[1].split(";")
router_inicial = (sys.argv[2], int(sys.argv[3]))
nombre_archivo = sys.argv[4] if len(sys.argv) == 5 else "mensajes.txt" # si no se da nombre de archivo, utilizamos el nombre mensaje.txt (más facil de runnear asi)

enviador = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Enviamos cada linea del archivo en paquetes separados
with open(nombre_archivo, encoding="utf-8") as archivo:
    for linea in archivo:
        linea = linea.rstrip("\r\n")
        paquete = {"ip": ip_final, "puerto": int(puerto_final), "ttl": int(ttl), "mensaje": linea}
        enviador.sendto(create_packet(paquete), router_inicial)
enviador.close()
