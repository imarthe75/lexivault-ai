import os
import logging
import hvac
from hvac.exceptions import InvalidRequest

class VaultClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.vault_url = os.getenv('VAULT_ADDR', 'http://vault:8200')
        self.token = os.getenv('VAULT_DEV_ROOT_TOKEN_ID', 'root')
        self.client = None
        self.is_connected = False

        self._connect()

    def _connect(self):
        try:
            self.client = hvac.Client(url=self.vault_url, token=self.token)
            if self.client.is_authenticated():
                self.is_connected = True
                self.logger.info(f"Conectado exitosamente a HashiCorp Vault en {self.vault_url}")
            else:
                self.logger.warning("No se pudo autenticar con HashiCorp Vault. Verifique el token.")
        except Exception as e:
            self.logger.error(f"Error al conectar con Vault: {e}")
            self.is_connected = False

    def get_secret(self, path, key, default=None):
        """
        Intenta obtener un secreto de Vault.
        Si falla o no está conectado, intenta obtenerlo de las variables de entorno (usando la clave como nombre de la variable).
        Si no existe, devuelve el valor por defecto.
        
        Args:
            path (str): Ruta del secreto en Vault (ej. 'secret/data/myapp')
            key (str): Clave del secreto dentro de la ruta (ej. 'DB_PASSWORD')
            default (any): Valor a devolver si no se encuentra.
        """
        value = None

        # 1. Intentar obtener de Vault
        if self.is_connected:
            try:
                # En Vault KV v2, los datos están bajo 'data' -> 'data'
                read_response = self.client.secrets.kv.v2.read_secret_version(path=path)
                value = read_response['data']['data'].get(key)
                if value:
                    self.logger.debug(f"Secreto '{key}' recuperado de Vault.")
            except InvalidRequest:
                self.logger.warning(f"Ruta de secreto no encontrada en Vault: {path}")
            except Exception as e:
                self.logger.error(f"Error al leer secreto '{key}' de Vault: {e}")

        # 2. Fallback a variables de entorno
        if value is None:
            self.logger.debug(f"Secreto '{key}' no encontrado en Vault (o desconectado). Buscando en variables de entorno.")
            value = os.getenv(key, default)

        return value

# Instancia global para usar en la app
vault_client = VaultClient()
