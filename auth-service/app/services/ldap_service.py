import logging
from ldap3 import Server, Connection, ALL, SIMPLE, Tls
from ldap3.core.exceptions import LDAPException, LDAPBindError, LDAPInvalidCredentialsResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class LDAPService:
    def authenticate(self, username: str, password: str) -> dict | None:
        try:
            tls = Tls() if settings.LDAP_USE_SSL else None
            server = Server(
                settings.LDAP_SERVER,
                use_ssl=settings.LDAP_USE_SSL,
                tls=tls,
                get_info=ALL,
            )

            with Connection(
                server,
                user=settings.LDAP_BIND_DN,
                password=settings.LDAP_BIND_PASSWORD,
                authentication=SIMPLE,
                auto_bind=True,
            ) as service_conn:
                search_filter = settings.LDAP_USER_SEARCH_FILTER.format(username=username)
                service_conn.search(
                    search_base=settings.LDAP_BASE_DN,
                    search_filter=search_filter,
                    attributes=["sAMAccountName", "mail", "displayName", "memberOf", "userAccountControl"],
                )

                if not service_conn.entries:
                    logger.warning(f"LDAP: utilisateur '{username}' introuvable.")
                    return None

                user_entry = service_conn.entries[0]
                user_dn = user_entry.entry_dn

                uac = int(str(user_entry.userAccountControl)) if user_entry.userAccountControl else 0
                if uac & 2:
                    logger.warning(f"LDAP: compte '{username}' désactivé.")
                    return None

            with Connection(server, user=user_dn, password=password, authentication=SIMPLE, auto_bind=True):
                logger.info(f"LDAP: auth réussie pour '{username}'.")
                return {
                    "username": str(user_entry.sAMAccountName),
                    "email": str(user_entry.mail) if user_entry.mail else None,
                    "display_name": str(user_entry.displayName) if user_entry.displayName else username,
                    "groups": [str(g) for g in user_entry.memberOf] if user_entry.memberOf else [],
                }

        except LDAPInvalidCredentialsResult:
            logger.warning(f"LDAP: mot de passe incorrect pour '{username}'.")
            return None
        except LDAPBindError as e:
            logger.error(f"LDAP: erreur bind — {e}")
            return None
        except LDAPException as e:
            logger.error(f"LDAP: erreur inattendue — {e}")
            raise


ldap_service = LDAPService()
