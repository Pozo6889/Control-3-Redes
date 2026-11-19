import sys
import socket
from funcionesAux import create_packet

# Recibir ip_final puerto_final ip_envio puerto_envio mensaje ttl(opcional)
if len(sys.argv) not in (6, 7):
    print('Uso: python hablador.py IP_final puerto_final IP_envio puerto_envio "mensaje" [ttl]')
    sys.exit(1)

ip_final = sys.argv[1]
puerto_final = int(sys.argv[2])
ip_envio = sys.argv[3]
puerto_envio = int(sys.argv[4])
mensaje = sys.argv[5]
ttl = int(sys.argv[6]) if len(sys.argv) == 7 else 64  # Si no se entrega ttl lo definimos como 64

# paquete a enviar con ip y puerto final, el mensaje y ttl
paquete = {"ip": ip_final, "puerto": puerto_final, "ttl": ttl, "mensaje": mensaje}
enviador = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
enviador.sendto(create_packet(paquete), (ip_envio, puerto_envio))
enviador.close()
