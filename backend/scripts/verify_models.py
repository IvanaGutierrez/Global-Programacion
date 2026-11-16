import sys
from decimal import Decimal
from sqlalchemy import inspect
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql
from sqlmodel import SQLModel

from app.core.database import (
    Editorial,
    Genero,
    Autor,
    Libro,
    LibroAutor,
    Cliente,
    PerfilCliente,
    Venta,
    RenglonVenta,
)

def verify():
    tables = SQLModel.metadata.tables
    print(f"Total de tablas registradas en SQLModel.metadata: {len(tables)}")
    
    pg_dialect = postgresql.dialect()
    
    print("\n=== VERIFICACIÓN DETALLADA DE ÍNDICES, FKs, RESTRICCIONES Y RELACIONES ===")
    
    # 1. Verificar índices en cada Foreign Key
    for table_name, table in tables.items():
        print(f"\nTabla: '{table_name}'")
        for fk in table.foreign_keys:
            col = fk.parent
            has_idx = col.index or any(col in idx.columns for idx in table.indexes) or col.primary_key
            status_idx = "OK (Indexada)" if has_idx else "ERROR (Falta índice)"
            print(f"  - FK: {col.name} -> {fk.target_fullname} | Indice: {status_idx}")
            assert has_idx, f"La columna FK {col.name} en {table_name} debe tener index=True"
            
        for col in table.columns:
            if col.unique:
                print(f"  - UNIQUE: {col.name}")
        
        for const in table.constraints:
            if type(const).__name__ == "CheckConstraint":
                print(f"  - CHECK: {const.name} -> {const.sqltext}")
                
    # 2. Verificar índices explícitos
    print("\n=== ÍNDICES GENERADOS ===")
    for table_name, table in tables.items():
        for idx in table.indexes:
            idx_ddl = CreateIndex(idx).compile(dialect=pg_dialect)
            print(f"  {idx_ddl}")
            
    # 3. Verificar uselist=False en Cliente.perfil
    cliente_mapper = inspect(Cliente)
    assert cliente_mapper.relationships["perfil"].uselist is False, "Cliente.perfil debe tener uselist=False"
    print("\n Relación 1 a 1: Cliente.perfil tiene uselist=False garantizado (objeto único o None).")
    
    # 4. Verificar tipos Decimal en dinero
    libro_precio_col = Libro.__table__.columns["precio"]
    renglon_precio_col = RenglonVenta.__table__.columns["precio_unitario"]
    venta_total_col = Venta.__table__.columns["total"]
    
    assert str(libro_precio_col.type) == "NUMERIC(10, 2)", f"libro.precio debe ser NUMERIC(10, 2), es {libro_precio_col.type}"
    assert str(renglon_precio_col.type) == "NUMERIC(10, 2)", f"renglon_venta.precio_unitario debe ser NUMERIC(10, 2), es {renglon_precio_col.type}"
    assert str(venta_total_col.type) == "NUMERIC(12, 2)", f"venta.total debe ser NUMERIC(12, 2), es {venta_total_col.type}"
    print(" Tipos de dinero: libro.precio NUMERIC(10,2), renglon.precio_unitario NUMERIC(10,2), venta.total NUMERIC(12,2).")

    # 5. Verificar back_populates en relaciones
    relationships_to_check = [
        (Editorial, "libros", "editorial"),
        (Genero, "libros", "genero"),
        (Autor, "autorias", "autor"),
        (Libro, "editorial", "libros"),
        (Libro, "genero", "libros"),
        (Libro, "autorias", "libro"),
        (Libro, "renglones", "libro"),
        (LibroAutor, "libro", "autorias"),
        (LibroAutor, "autor", "autorias"),
        (Cliente, "perfil", "cliente"),
        (Cliente, "ventas", "cliente"),
        (PerfilCliente, "cliente", "perfil"),
        (Venta, "cliente", "ventas"),
        (Venta, "renglones", "venta"),
        (RenglonVenta, "venta", "renglones"),
        (RenglonVenta, "libro", "renglones"),
    ]
    
    print("\n=== VERIFICANDO NAVEGACIÓN BIDIRECCIONAL (back_populates) ===")
    for model, rel_name, expected_back in relationships_to_check:
        rel = model.__sqlmodel_relationships__[rel_name]
        back = rel.back_populates
        assert back == expected_back, f"{model.__name__}.{rel_name} back_populates es {back}, se esperaba {expected_back}"
        print(f"  - {model.__name__}.{rel_name} <---> back_populates='{back}' [OK]")

    print("\n Todas las validaciones de modelos, tipos, relaciones y restricciones fueron superadas exitosamente.")

if __name__ == "__main__":
    verify()
