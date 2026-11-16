import sys
import socket
from funcionesAux import create_packet
# Recibir IP y puerto desde el .txt
if len(sys.argv) != 6:
    print('Uso: python3 enviar.py IP_final puerto_final IP_envio puerto_envio "mensaje"')
    sys.exit(1)
## Forma de runnear python router5.py IP_final puerto_final IP_envio puerto_envio "mensaje"    
ip_final = sys.argv[1]
puerto_final = int(sys.argv[2])
ip_envio = sys.argv[3]
puerto_envio = int(sys.argv[4])
mensaje = sys.argv[5]


## paquete a enviar con ip y puerto final y el mensaje
paquete = {"ip": ip_final, "puerto": puerto_final, "mensaje": mensaje}
paquete_listoco = create_packet(paquete)
### Socket No orientaado a conexion que esta escuchando
enviador = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
enviador.sendto(paquete_listoco, (ip_envio, puerto_envio))
buffer = 512

enviador.close()