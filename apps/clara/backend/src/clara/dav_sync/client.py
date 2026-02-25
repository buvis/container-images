"""Thin wrapper around caldav lib + raw HTTP for CardDAV."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

import caldav
import requests
import vobject
from icalendar import Calendar


@dataclass
class DavResource:
    """A remote DAV resource (vCard, VEVENT, VTODO)."""

    uid: str
    href: str
    etag: str | None
    data: str  # raw vCard/iCal text


class DavClient:
    """Client for CalDAV/CardDAV operations."""

    def __init__(self, url: str, username: str, password: str) -> None:
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self._caldav_client: caldav.DAVClient | None = None

    def _get_caldav(self) -> caldav.DAVClient:
        if self._caldav_client is None:
            self._caldav_client = caldav.DAVClient(
                url=self.url, username=self.username, password=self.password
            )
        return self._caldav_client

    def _resolve_url(self, href: str) -> str:
        """Resolve a possibly-relative href against the server base URL."""
        if href.startswith("http"):
            return href
        return urljoin(self.url + "/", href)

    # -- Connection test --

    def test_connection(self) -> dict[str, str | None]:
        """Test connection and discover collections.

        Returns dict with carddav_path, caldav_path if found.
        """
        result: dict[str, str | None] = {
            "carddav_path": None,
            "caldav_path": None,
        }
        client = self._get_caldav()
        principal = client.principal()
        calendars = principal.calendars()
        if calendars:
            result["caldav_path"] = str(calendars[0].url)
        # CardDAV: try well-known or principal addressbooks
        try:
            for ab in _discover_addressbooks(self.url, self.username, self.password):
                result["carddav_path"] = ab
                break
        except Exception:
            pass
        return result

    # -- CardDAV operations --

    def list_vcards(self, carddav_path: str) -> list[DavResource]:
        """List all vCards from a CardDAV addressbook."""
        resources: list[DavResource] = []
        report_url = self._resolve_url(carddav_path)
        resp = requests.request(
            "REPORT",
            report_url,
            auth=(self.username, self.password),
            headers={"Content-Type": "application/xml; charset=utf-8", "Depth": "1"},
            data=_ADDRESSBOOK_QUERY,
            timeout=30,
        )
        resp.raise_for_status()
        # Parse multistat response
        for href, etag, data in _parse_multistatus(resp.text):
            if not data:
                continue
            uid = _extract_vcard_uid(data)
            if uid:
                resources.append(
                    DavResource(
                        uid=uid,
                        href=self._resolve_url(href),
                        etag=etag,
                        data=data,
                    )
                )
        return resources

    def put_vcard(
        self, carddav_path: str, uid: str, vcard_text: str, etag: str | None = None
    ) -> str | None:
        """Create or update a vCard. Returns new etag."""
        url = f"{carddav_path.rstrip('/')}/{uid}.vcf"
        headers: dict[str, str] = {"Content-Type": "text/vcard; charset=utf-8"}
        if etag:
            headers["If-Match"] = etag
        resp = requests.put(
            url,
            auth=(self.username, self.password),
            headers=headers,
            data=vcard_text.encode("utf-8"),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.headers.get("ETag")

    def delete_vcard(self, href: str, etag: str | None = None) -> None:
        """Delete a vCard by href."""
        headers: dict[str, str] = {}
        if etag:
            headers["If-Match"] = etag
        resp = requests.delete(
            self._resolve_url(href),
            auth=(self.username, self.password),
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()

    # -- CalDAV operations --

    def list_events(self, caldav_path: str) -> list[DavResource]:
        """List all VEVENT/VTODO from a CalDAV calendar."""
        client = self._get_caldav()
        cal = caldav.Calendar(client=client, url=caldav_path)
        resources: list[DavResource] = []
        for obj in cal.objects():
            data = obj.data
            if not data:
                continue
            uid = _extract_ical_uid(data)
            if uid:
                resources.append(
                    DavResource(
                        uid=uid,
                        href=str(obj.url),
                        etag=getattr(obj, "etag", None),
                        data=data,
                    )
                )
        return resources

    def put_event(self, caldav_path: str, uid: str, ical_text: str) -> str | None:
        """Create or update a calendar object."""
        client = self._get_caldav()
        cal = caldav.Calendar(client=client, url=caldav_path)
        obj = cal.save_event(ical_text)
        return getattr(obj, "etag", None)

    def delete_event(self, href: str) -> None:
        """Delete a calendar object by href."""
        client = self._get_caldav()
        obj = caldav.CalendarObjectResource(client=client, url=href)
        obj.delete()


# -- Helpers --

_ADDRESSBOOK_QUERY = """<?xml version="1.0" encoding="utf-8"?>
<C:addressbook-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
  <D:prop>
    <D:getetag/>
    <C:address-data/>
  </D:prop>
</C:addressbook-query>"""


def _discover_addressbooks(url: str, username: str, password: str) -> list[str]:
    """Try to discover CardDAV addressbooks via PROPFIND."""
    resp = requests.request(
        "PROPFIND",
        url,
        auth=(username, password),
        headers={"Content-Type": "application/xml; charset=utf-8", "Depth": "1"},
        data="""<?xml version="1.0" encoding="utf-8"?>
        <D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
          <D:prop><D:resourcetype/></D:prop>
        </D:propfind>""",
        timeout=30,
    )
    resp.raise_for_status()
    import defusedxml.ElementTree as ET

    root = ET.fromstring(resp.text)
    ns = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:carddav"}
    paths: list[str] = []
    for response in root.findall(".//D:response", ns):
        href_el = response.find("D:href", ns)
        restype = response.find(".//D:resourcetype", ns)
        if (
            restype is not None
            and restype.find("C:addressbook", ns) is not None
            and href_el is not None
            and href_el.text
        ):
            paths.append(href_el.text)
    return paths


def _parse_multistatus(xml_text: str) -> list[tuple[str, str | None, str | None]]:
    """Parse WebDAV multistatus XML into (href, etag, data) tuples."""
    import defusedxml.ElementTree as ET

    root = ET.fromstring(xml_text)
    ns = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:carddav"}
    results: list[tuple[str, str | None, str | None]] = []
    for response in root.findall(".//D:response", ns):
        href_el = response.find("D:href", ns)
        href = href_el.text if href_el is not None else ""
        etag_el = response.find(".//D:getetag", ns)
        etag = etag_el.text.strip('"') if etag_el is not None and etag_el.text else None
        data_el = response.find(".//C:address-data", ns)
        data = data_el.text if data_el is not None else None
        results.append((href or "", etag, data))
    return results


def _extract_vcard_uid(vcard_text: str) -> str | None:
    """Extract UID from vCard text."""
    try:
        vc = vobject.readOne(vcard_text)
        if hasattr(vc, "uid"):
            return vc.uid.value
    except Exception:
        pass
    return None


def _extract_ical_uid(ical_text: str) -> str | None:
    """Extract UID from iCalendar text."""
    try:
        cal = Calendar.from_ical(ical_text)
        for component in cal.walk():
            uid = component.get("uid")
            if uid:
                return str(uid)
    except Exception:
        pass
    return None
