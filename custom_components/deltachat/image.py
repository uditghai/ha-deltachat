import logging
import datetime
from homeassistant.components.image import ImageEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from .const import DOMAIN
import segno
import io

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback):
    """Set up the image entities from a config entry."""
    account = entry.runtime_data["account"]
    async_add_entities([DeltaChatQRCodeImageEntity(hass, entry,account)])

class DeltaChatQRCodeImageEntity(ImageEntity):
    """Representation of an Image Entity displayed on the device page."""

    def __init__(self, hass, entry,account) -> None:
        """Initialize the image entity."""
        super().__init__(hass)
        self._account = account
        self._attr_name = "QR Code"
        self._attr_unique_id = f"{entry.entry_id}_qr_code_image"
        svg_tuple = self._account.get_qr_code_svg()
        if svg_tuple and svg_tuple[1]:
            self._image_svg = svg_tuple[1].encode("utf-8")
        self._last_updated = datetime.datetime.now()

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)}
        )

    @property
    def content_type(self) -> str:
        """Return the correct content type for vector graphics."""
        return "image/svg+xml"

    def image(self) -> bytes | None:
        """Return bytes of image."""
        if self._image_svg:
            return self._image_svg

    @property
    def image_last_updated(self) -> datetime.datetime | None:
        """Return when the image was last updated to break frontend caching."""
        return self._last_updated
