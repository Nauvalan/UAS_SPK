from sqlalchemy import Float
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class data_toko(Base):
    __tablename__ = 'data_toko'
    nama_toko: Mapped[str] = mapped_column(primary_key=True)
    kelengkapan_barang: Mapped[int] = mapped_column()
    lama_kadaluarsa: Mapped[int] = mapped_column()
    harga_rata_rata: Mapped[int] = mapped_column()
    jarak_supplier: Mapped[int] = mapped_column()
    jarak_transportasi: Mapped[int] = mapped_column()
    
    def __repr__(self) -> str:
        return f"data_toko(nama_toko={self.nama_toko!r}, kelengkapan_barang={self.kelengkapan_barang!r})"