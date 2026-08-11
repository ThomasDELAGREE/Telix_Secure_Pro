"""
Authentification visiteur par numero de chambre (deploiement hotelier).

HYPOTHESE A VALIDER : ce service valide un code d'acces statique associe a une
chambre (table room_codes). Dans un deploiement reel, ce code serait genere/
renouvele automatiquement par le PMS hotelier a chaque sejour ; a adapter selon
l'integration retenue (Odoo PMS, Mews, Opera...).
"""
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.room_code import RoomCode

logger = logging.getLogger(__name__)


class RoomService:
    def authenticate(self, db: Session, room_number: str, access_code: str) -> bool:
        room = db.query(RoomCode).filter(RoomCode.room_number == room_number).first()

        if room is None:
            logger.warning(f"Chambre '{room_number}' inconnue.")
            return False

        if not room.active:
            logger.warning(f"Chambre '{room_number}' inactive.")
            return False

        if room.access_code != access_code:
            logger.warning(f"Code d'acces incorrect pour la chambre '{room_number}'.")
            return False

        now = datetime.now(timezone.utc)
        if room.valid_from and now < room.valid_from:
            return False
        if room.valid_until and now > room.valid_until:
            return False

        logger.info(f"Authentification reussie pour la chambre '{room_number}'.")
        return True


room_service = RoomService()
