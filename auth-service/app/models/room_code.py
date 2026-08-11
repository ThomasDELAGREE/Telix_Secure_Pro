from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime, timezone
from app.core.database import Base


class RoomCode(Base):
    """
    Table de reference pour l'authentification visiteur par numero de chambre
    (deploiement hotelier). Provisionnee manuellement ou via integration PMS.

    HYPOTHESE A VALIDER : ce modele suppose une gestion manuelle/CSV des codes.
    Une integration avec un PMS hotelier (ex: Odoo, Mews, Opera) permettrait
    de synchroniser automatiquement les codes a l'arrivee/depart des clients.
    """
    __tablename__ = "room_codes"

    room_number = Column(String(50), primary_key=True)
    access_code = Column(String(50), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
