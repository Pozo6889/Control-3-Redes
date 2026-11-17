import sys
import socket
from funcionesAux import create_packet, fragment_IP_packet

# Uso: python enviar_fragmentos.py IP_router puerto_router modo
# Envia a mano los fragmentos de 2 paquetes distintos (ID 111 y ID 222) dirigidos a ese mismo router.
# Modos: orden | desorden | intercalado | incompleto | resto
MTU = 50  # 30 bytes de mensaje por fragmento

if len(sys.argv) != 4 or sys.argv[3] not in ("orden", "desorden", "intercalado", "incompleto", "resto"):
    print("Uso: python enviar_fragmentos.py IP_router puerto_router modo")
    print("Modos: orden | desorden | intercalado | incompleto | resto")
    sys.exit(1)

router = (sys.argv[1], int(sys.argv[2]))
modo = sys.argv[3]


def fragmentos_de(id_paquete, mensaje):
    paquete = create_packet({"ip": router[0], "puerto": router[1], "ttl": 10, "id": id_paquete,
                             "offset": 0, "tamano": len(mensaje), "flag": 0, "mensaje": mensaje})
    return fragment_IP_packet(paquete, MTU)


A = fragmentos_de(111, ("Mensaje A (ID 111): " + "a" * 80).encode())   # 100 bytes -> 4 fragmentos
B = fragmentos_de(222, ("Mensaje B (ID 222): " + "b" * 60).encode())   # 80 bytes  -> 3 fragmentos

if modo == "orden":
    envio = A + B
elif modo == "desorden":
    envio = A[::-1] + [B[1], B[2], B[0]]
elif modo == "intercalado":
    envio = []
    for i in range(max(len(A), len(B))):  # A al reves intercalado con B en orden
        if i < len(A):
            envio.append(A[::-1][i])
        if i < len(B):
            envio.append(B[i])
elif modo == "incompleto":
    envio = A + B[:-1]  # B queda sin su ultimo fragmento
else:  # resto
    envio = [B[-1]]

enviador = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for fragmento in envio:
    enviador.sendto(fragmento, router)
enviador.close()
print(f"Enviados {len(envio)} fragmentos en modo '{modo}'")
