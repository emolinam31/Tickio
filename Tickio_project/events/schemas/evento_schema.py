from pydantic import BaseModel, field_validator
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List


class CategoriaEventoSchema(BaseModel):
    """Schema para Categoría de Evento"""
    id: int
    nombre: str
    descripcion: str

    class Config:
        from_attributes = True


class TicketTypeSchema(BaseModel):
    """Schema para Tipo de Boleto"""
    id: int
    name: str
    price: Decimal
    capacity: int
    sold: int
    active: bool

    @field_validator('price', mode='before')
    @classmethod
    def validate_price(cls, v):
        """Validar que el precio sea un Decimal válido"""
        if v is None:
            return Decimal('0.00')
        try:
            decimal_value = Decimal(str(v))
            if decimal_value < 0:
                return Decimal('0.00')
            return decimal_value
        except (ValueError, TypeError):
            return Decimal('0.00')

    @property
    def available(self) -> int:
        return max(self.capacity - self.sold, 0)

    class Config:
        from_attributes = True


class EventoSchema(BaseModel):
    """Schema básico para Evento"""
    id: int
    nombre: str
    fecha: date
    lugar: str
    precio: Decimal
    cupos_disponibles: int
    estado: str

    @field_validator('precio', mode='before')
    @classmethod
    def validate_precio(cls, v):
        """Validar que el precio sea un Decimal válido"""
        if v is None:
            return Decimal('0.00')
        try:
            decimal_value = Decimal(str(v))
            if decimal_value < 0:
                return Decimal('0.00')
            return decimal_value
        except (ValueError, TypeError):
            return Decimal('0.00')

    class Config:
        from_attributes = True


class EventoListaSchema(BaseModel):
    """Schema para listar eventos con información básica"""
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha: date
    lugar: str
    precio: Decimal
    cupos_disponibles: int
    estado: str
    categoria: CategoriaEventoSchema
    organizador_id: Optional[int]
    organizador_nombre: Optional[str] = None
    fecha_creacion: datetime
    ticket_types_count: int = 0

    @field_validator('precio', mode='before')
    @classmethod
    def validate_precio(cls, v):
        """Validar que el precio sea un Decimal válido"""
        if v is None:
            return Decimal('0.00')
        try:
            decimal_value = Decimal(str(v))
            if decimal_value < 0:
                return Decimal('0.00')
            return decimal_value
        except (ValueError, TypeError):
            return Decimal('0.00')

    class Config:
        from_attributes = True


class EventoDetailSchema(BaseModel):
    """Schema detallado para un evento individual"""
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha: date
    lugar: str
    precio: Decimal
    cupos_disponibles: int
    estado: str
    categoria: CategoriaEventoSchema
    organizador_id: Optional[int]
    organizador_nombre: Optional[str] = None
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    ticket_types: List[TicketTypeSchema] = []
    total_disponible: int = 0
    precio_minimo: Optional[Decimal] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    @field_validator('precio', 'precio_minimo', mode='before')
    @classmethod
    def validate_precios(cls, v):
        """Validar que los precios sean Decimales válidos"""
        if v is None:
            return None
        try:
            decimal_value = Decimal(str(v))
            if decimal_value < 0:
                return Decimal('0.00')
            return decimal_value
        except (ValueError, TypeError):
            return None

    class Config:
        from_attributes = True
