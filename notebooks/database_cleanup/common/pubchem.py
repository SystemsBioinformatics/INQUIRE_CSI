"""Rate-limited PubChem PUG REST client shared by the source-database cleanup notebooks.

Requests are paced globally (thread-safe) at ``max_req_per_sec`` and slowed down further when PubChem's
``X-Throttling-Control`` header reports yellow/red/black load status.

    client = PubChemClient(max_req_per_sec=4)
    client.name_lookup("caffeine")            # -> (CID, Title, IUPACName, InChIKey) or None
    client.batch_by_inchikey([...])           # -> {inchikey: (Title, IUPACName, InChIKey)}
"""

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

import pandas as pd
import requests

from .cleaning import append_cache, clean_value, load_cache
from .utils import print_overwrite, ts

PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound"
PROPS = "Title,IUPACName,InChIKey"  # CID is always included in the property table


class PubChemClient:
    def __init__(self, max_req_per_sec=4, props=PROPS, timeout=60):
        self.max_req_per_sec = max_req_per_sec
        self.props = props
        self.timeout = timeout
        self.extra_delay = 0.0  # seconds added to the base interval; set from the throttle header
        self.stats = {"n": 0, "secs": 0.0}  # requests made and cumulative time spent on responses
        self._lock = threading.Lock()
        self._last_call = 0.0

    def _throttle(self):
        with self._lock:
            wait = self._last_call + 1.0 / self.max_req_per_sec + self.extra_delay - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()

    def _read_throttle_header(self, res):
        """Adjust pacing from X-Throttling-Control, e.g.
        'Request Count status: Green (0%), Request Time status: Green (0%), ...'.
        The worst reported colour (green < yellow < red < black) sets the extra delay between requests."""
        hdr = res.headers.get("X-Throttling-Control", "").lower()
        if "black" in hdr:
            self.extra_delay = 30.0
        elif "red" in hdr:
            self.extra_delay = 5.0
        elif "yellow" in hdr:
            self.extra_delay = 1.0
        elif hdr:
            self.extra_delay = max(0.0, self.extra_delay / 2 - 0.05)  # decay to baseline when green

    def request(self, method, url, data=None, retries=5):
        """Return a 200 Response, None for 404/400 or an unparseable query (nothing found); raise RuntimeError after repeated failures."""
        for attempt in range(retries):
            self._throttle()
            t0 = time.monotonic()
            try:
                res = requests.request(method, url, data=data, timeout=self.timeout)
            except requests.RequestException:
                time.sleep(2**attempt)
                continue
            with self._lock:
                self.stats["n"] += 1
                self.stats["secs"] += time.monotonic() - t0
            self._read_throttle_header(res)
            if res.status_code == 200:
                return res
            if res.status_code == 404:
                return None
            if res.status_code == 400 or (res.status_code == 500 and "URL arguments" in res.text):
                return None  # PubChem cannot parse this query (deterministic); retrying never helps, so treat as not found
            time.sleep(2**attempt * (5 if res.status_code in (429, 503) else 1))  # server busy: back off harder
        raise RuntimeError(f"PubChem request failed after retries: {url}")

    @staticmethod
    def _properties(res):
        return res.json().get("PropertyTable", {}).get("Properties", []) if res is not None else []

    def _first_row(self, res):
        """First compound of a property-table response as a dict (CID plus the requested properties), or None."""
        props = self._properties(res)
        return props[0] if props else None  # first CID wins if the query matches several

    def _first_property(self, res):
        """First compound of a property-table response as (CID, Title, IUPACName, InChIKey), or None."""
        p = self._first_row(res)
        if p is None:
            return None
        return p.get("CID"), p.get("Title"), p.get("IUPACName"), p.get("InChIKey")

    def name_lookup(self, name):
        """Single-name GET (names/CAS numbers can contain commas and special characters, so are URL-quoted).
        Returns (CID, Title, IUPACName, InChIKey) or None."""
        url = f"{PUG}/name/{quote(str(name), safe='')}/property/{self.props}/JSON"
        return self._first_property(self.request("GET", url))

    def name_lookup_row(self, name):
        """Like ``name_lookup`` but returns the whole property row as a dict (all properties requested through
        ``props``, e.g. ``PubChemClient(props="Title,IUPACName,InChIKey,SMILES")``), or None if nothing is found."""
        url = f"{PUG}/name/{quote(str(name), safe='')}/property/{self.props}/JSON"
        return self._first_row(self.request("GET", url))

    def smiles_lookup(self, smiles):
        """SMILES via POST, because SMILES contain characters (/, #, etc.) that are awkward in a URL path.
        Returns (CID, Title, IUPACName, InChIKey) or None."""
        url = f"{PUG}/smiles/property/{self.props}/JSON"
        return self._first_property(self.request("POST", url, data={"smiles": smiles}))

    def smiles_lookup_row(self, smiles):
        """Like ``smiles_lookup`` but returns the whole property row as a dict, or None if nothing is found."""
        url = f"{PUG}/smiles/property/{self.props}/JSON"
        return self._first_row(self.request("POST", url, data={"smiles": smiles}))

    def batch_by_inchikey(self, keys):
        """POST a list of InChIKeys; return {inchikey: (Title, IUPACName, InChIKey)} for those found.
        The property table carries the CID and the matched InChIKey, so InChIKey->CID resolution and property
        retrieval happen in one request. A 404 means no key in the batch matched (or one invalid key spoiled
        it), so the batch is bisected until the culprits are isolated."""
        keys = list(keys)
        if not keys:
            return {}
        res = self.request("POST", f"{PUG}/inchikey/property/{self.props}/JSON", data={"inchikey": ",".join(keys)})
        if res is None:
            if len(keys) == 1:
                return {}
            mid = len(keys) // 2
            return {**self.batch_by_inchikey(keys[:mid]), **self.batch_by_inchikey(keys[mid:])}
        out = {}
        for p in self._properties(res):
            ik = p.get("InChIKey")
            if ik and ik not in out:  # first CID wins if a key maps to several
                out[ik] = (p.get("Title"), p.get("IUPACName"), ik)
        return out


# ---------------------------------------------------------------------------
# Cached, resumable lookup of the unique identifier sets of a source database
# ---------------------------------------------------------------------------
# PubChem property -> cache column
_PROP_TO_COLUMN = {
    "Title": "Name_PubChem",
    "IUPACName": "IUPACName_PubChem",
    "InChIKey": "InChIKey_PubChem",
    "SMILES": "SMILES_PubChem",
}


def lookup_attempts(uid, attempts):
    """Try the identifiers of one compound in order and return the first hit as a cache record.

    ``attempts`` is a list of ``(method, query, lookup_row_func)``, e.g.
    ``[("CAS", cas, client.name_lookup_row), ("SMILES", smiles, client.smiles_lookup_row)]``. Missing values and
    placeholders are skipped. Compounds with no usable query, or no hit, are returned as 'not_found' (and so
    cached). Returns None only on a transient failure, so that a re-run retries it.
    The record has ``uid``, ``CID``, ``Lookup_method`` and one ``<property>_PubChem`` column per property the
    client requested (Name, IUPACName, InChIKey, SMILES); the cache keeps the columns listed in ``cache_cols``.
    """
    try:
        for method, query, func in attempts:
            query = clean_value(query)
            if query is None:
                continue
            hit = func(query)
            if hit:
                rec = {"uid": uid, "CID": hit.get("CID"), "Lookup_method": method}
                rec.update({col: hit.get(prop) for prop, col in _PROP_TO_COLUMN.items()})
                return rec
    except RuntimeError:
        return None
    return {"uid": uid, "CID": None, "Lookup_method": "not_found", **{col: None for col in _PROP_TO_COLUMN.values()}}


def per_row(lookup_compound, n_workers=4):
    """Turn a one-row lookup function into a chunk function that runs the rows in parallel and drops transient
    failures (None)."""

    def lookup_chunk(chunk):
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            return [r for r in ex.map(lookup_compound, chunk) if r is not None]

    return lookup_chunk


def run_cached_lookup(df_unique, row_cols, lookup_chunk, cache_path, cache_cols, client, chunk=200, limit=None):
    """Resumable PubChem lookup for ``df_unique`` (one row per ``uid``, see ``cleaning.add_uid``).

    Rows whose uid is already in the cache at ``cache_path`` are skipped. The others are passed to
    ``lookup_chunk`` ``chunk`` rows at a time, as tuples ``(uid, *row_cols)``; it returns a list of records
    (dicts with a ``uid``), which are appended to the cache after every chunk, so it is safe to interrupt and
    re-run. Prints progress with an ETA based on measured throughput. Returns the cache restricted to the uids
    of ``df_unique``.
    """
    cache = load_cache(cache_path, cache_cols)
    done_ids = set(cache["uid"]) & set(df_unique["uid"])  # only cache entries that match a current identifier set
    n_stale = cache["uid"].nunique() - len(done_ids)

    todo = df_unique.loc[~df_unique["uid"].isin(done_ids), ["uid", *row_cols]]
    if limit:
        todo = todo.head(limit)
    rows = list(todo.itertuples(index=False, name=None))
    print(f"{len(done_ids):,} of {len(df_unique):,} compounds already cached, {len(rows):,} to look up | {ts()}")
    if n_stale:
        print(f"({n_stale:,} cache entries match no current identifier set and are ignored.)")
    print("No up-front time estimate: an Estimated Time of Arrival based on measured throughput is shown while running.")
    print("It is safe to interrupt and re-run.\n")

    rate = None  # smoothed compounds/second
    for start in range(0, len(rows), chunk):
        t0 = time.monotonic()
        batch = rows[start:start + chunk]
        append_cache(cache_path, lookup_chunk(batch), cache_cols)
        inst = len(batch) / (time.monotonic() - t0)
        rate = inst if rate is None else 0.7 * rate + 0.3 * inst  # exponential smoothing of recent chunks
        done = min(start + chunk, len(rows))
        eta_min = (len(rows) - done) / rate / 60
        avg_lat = client.stats["secs"] / max(client.stats["n"], 1)
        print_overwrite(
            f"Looked up {done:,} / {len(rows):,} | {rate:.1f} cpd/s | ETA ~{eta_min:.0f} min | "
            f"{client.stats['n']:,} requests, avg {avg_lat:.1f}s each | throttle +{client.extra_delay:.1f}s | "
            f"{time.strftime('%H:%M:%S')}"
        )

    cache = load_cache(cache_path, cache_cols).drop_duplicates("uid", keep="last")
    cache_current = cache[cache["uid"].isin(df_unique["uid"])]
    print(f"\n\nCached compounds: {len(cache_current):,} of {len(df_unique):,}")
    print(f"Resolved to an InChIKey: {cache_current['InChIKey_PubChem'].notna().sum():,}")
    if "Lookup_method" in cache_current.columns:
        print("Lookup method:")
        print(cache_current["Lookup_method"].value_counts().to_string())
    print(f"\nPubChem retrieval done | {ts()}\n")
    return cache_current
