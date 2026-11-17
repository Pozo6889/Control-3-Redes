import sys
import socket
import random
from funcionesAux import create_packet

# Uso: python hablador.py IP_final puerto_final IP_envio puerto_envio "mensaje" [ttl] [id]
if len(sys.argv) not in (6, 7, 8):
    print('Uso: python hablador.py IP_final puerto_final IP_envio puerto_envio "mensaje" [ttl] [id]')
    sys.exit(1)

ip_final = sys.argv[1]
puerto_final = int(sys.argv[2])
ip_envio = sys.argv[3]
puerto_envio = int(sys.argv[4])
mensaje = sys.argv[5]
ttl = int(sys.argv[6]) if len(sys.argv) >= 7 else 64  # TTL por defecto: 64
id_paquete = int(sys.argv[7]) if len(sys.argv) == 8 else random.randint(0, 2**32 - 1)  # ID aleatorio por defecto

mensaje_bytes = mensaje.encode()
paquete = {"ip": ip_final, "puerto": puerto_final, "ttl": ttl,
           "id": id_paquete, "offset": 0,
           "tamano": len(mensaje_bytes), "flag": 0, "mensaje": mensaje_bytes}
enviador = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
enviador.sendto(create_packet(paquete), (ip_envio, puerto_envio))
enviador.close()