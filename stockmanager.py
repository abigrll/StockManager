
import sqlite3
from datetime import datetime

# Base de datos local
conexion = sqlite3.connect("stockmanager.db")
conexion.execute("PRAGMA foreign_keys = ON")
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS producto (
    id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS movimiento (
    id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producto INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('ENTRADA','SALIDA')),
    cantidad INTEGER NOT NULL CHECK(cantidad > 0),
    fecha TEXT NOT NULL,
    sincronizado INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(id_producto) REFERENCES producto(id_producto)
)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_mov_pendiente
ON movimiento(sincronizado, fecha)
""")
conexion.commit()


class MovimientoDAO:
    def insertar(self, codigo, tipo, cantidad):
        producto = conexion.execute(
            "SELECT id_producto FROM producto WHERE codigo=?",
            (codigo,)
        ).fetchone()

        if not producto:
            print("Producto no encontrado.")
            return

        if tipo not in ("ENTRADA", "SALIDA") or cantidad <= 0:
            print("Datos incorrectos.")
            return

        conexion.execute("""
            INSERT INTO movimiento
            (id_producto, tipo, cantidad, fecha)
            VALUES (?, ?, ?, ?)
        """, (producto[0], tipo, cantidad,
              datetime.now().isoformat(timespec="seconds")))
        conexion.commit()
        print("Movimiento guardado correctamente.")

    def consultar(self):
        datos = conexion.execute("""
            SELECT m.id_movimiento, p.codigo, p.nombre,
                   m.tipo, m.cantidad, m.fecha,
                   m.sincronizado
            FROM movimiento m
            JOIN producto p ON m.id_producto = p.id_producto
            ORDER BY m.fecha DESC
        """).fetchall()

        if not datos:
            print("No hay movimientos registrados.")

        for dato in datos:
            print(dato)

    def actualizar(self, id_movimiento, cantidad):
        if cantidad <= 0:
            print("La cantidad debe ser positiva.")
            return

        resultado = conexion.execute("""
            UPDATE movimiento
            SET cantidad=?, sincronizado=0
            WHERE id_movimiento=?
        """, (cantidad, id_movimiento))
        conexion.commit()
        print("Actualizado." if resultado.rowcount else "No encontrado.")

    def eliminar(self, id_movimiento):
        resultado = conexion.execute(
            "DELETE FROM movimiento WHERE id_movimiento=?",
            (id_movimiento,)
        )
        conexion.commit()
        print("Eliminado." if resultado.rowcount else "No encontrado.")


dao = MovimientoDAO()

while True:
    print("\n===== STOCKMANAGER =====")
    print("1. Registrar producto")
    print("2. Registrar entrada")
    print("3. Registrar salida")
    print("4. Consultar movimientos")
    print("5. Actualizar movimiento")
    print("6. Eliminar movimiento")
    print("7. Salir")

    opcion = input("Selecciona una opcion: ")

    try:
        if opcion == "1":
            codigo = input("Codigo: ").strip()
            nombre = input("Nombre: ").strip()
            if not codigo or not nombre:
                print("Completa los datos.")
                continue
            conexion.execute(
                "INSERT INTO producto(codigo,nombre) VALUES(?,?)",
                (codigo, nombre)
            )
            conexion.commit()
            print("Producto registrado.")

        elif opcion in ("2", "3"):
            codigo = input("Codigo del producto: ")
            cantidad = int(input("Cantidad: "))
            tipo = "ENTRADA" if opcion == "2" else "SALIDA"
            dao.insertar(codigo, tipo, cantidad)

        elif opcion == "4":
            dao.consultar()

        elif opcion == "5":
            id_mov = int(input("ID del movimiento: "))
            cantidad = int(input("Nueva cantidad: "))
            dao.actualizar(id_mov, cantidad)

        elif opcion == "6":
            id_mov = int(input("ID del movimiento: "))
            dao.eliminar(id_mov)

        elif opcion == "7":
            conexion.close()
            print("Hasta luego.")
            break

        else:
            print("Opcion no valida.")

    except ValueError:
        print("Introduce un numero valido.")
    except sqlite3.IntegrityError as error:
        print("No se pudo guardar:", error)
