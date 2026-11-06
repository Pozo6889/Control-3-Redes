import sys

# Uso: python3 actividad1.py router_IP router_puerto router_rutas.txt
if len(sys.argv) != 4:
    print("Uso: python3 actividad1.py router_IP router_puerto router_rutas.txt")
    sys.exit(1)

router_ip = sys.argv[1]
router_puerto = int(sys.argv[2])  # sys.argv entrega strings, el puerto debe ser int
router_rutas = sys.argv[3]

print(f"Router escuchando en: ({router_ip}, {router_puerto})")
print(f"Tabla de rutas: {router_rutas}")