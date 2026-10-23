# impl: FR-001-03, FR-001-11
"""Завантаження і валідація версіонованого конфігу експерименту.

Контракт: specs/001-pipeline-safety/contracts/config.md.
Жодного секрету всередині: rpc-поля лише `env:`-посилання.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class ConfigError(ValueError):
    """Порушення схеми конфігу. Повідомлення завжди називає поле."""


@dataclass(frozen=True)
class ValidatorRef:
    identity: str
    label: str
    expected_client: str


@dataclass(frozen=True)
class BatchParams:
    tx_per_batch: int = 10
    cu_limit: int = 200_000
    cu_price_lamports: int = 0


@dataclass(frozen=True)
class RpcRefs:
    http_url_ref: str = "env:RPC_URL"
    ws_url_ref: str = "env:WS_URL"


@dataclass(frozen=True)
class RunConfig:
    config_version: str
    spend_cap_lamports: int
    base_fee_lamports: int = 5000
    batch: BatchParams = field(default_factory=BatchParams)
    validators: tuple = ()
    rpc: RpcRefs = field(default_factory=RpcRefs)


def _fail(field_name: str, why: str) -> ConfigError:
    return ConfigError(f"{field_name}: {why}")


def _as_dict(source) -> dict:
    if isinstance(source, dict):
        return source
    p = Path(source)
    if not p.is_file():
        raise _fail("config", f"файл не знайдено: {p}")
    try:
        import yaml  # type: ignore
    except ImportError as e:
        raise _fail("config", "для YAML-файлу потрібен pyyaml в образі") from e
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise _fail("config", "корінь YAML мусить бути мапою")
    return data


def load(source) -> RunConfig:
    """Завантажити RunConfig з dict або YAML-файлу. Кидає ConfigError з полем."""
    d = _as_dict(source)

    version = d.get("config_version")
    if not version or not isinstance(version, str):
        raise _fail("config_version", "обов'язкове непорожнє string")

    if "spend_cap_lamports" not in d:
        raise _fail("spend_cap_lamports", "обов'язкове, int >= 0")
    cap = d["spend_cap_lamports"]
    if not isinstance(cap, int) or isinstance(cap, bool) or cap < 0:
        raise _fail("spend_cap_lamports", "має бути int >= 0")

    base_fee = d.get("base_fee_lamports", 5000)
    if not isinstance(base_fee, int) or isinstance(base_fee, bool) or base_fee <= 0:
        raise _fail("base_fee_lamports", "має бути int > 0")

    b = d.get("batch", {}) or {}
    try:
        n = int(b.get("tx_per_batch", 10))
    except (TypeError, ValueError):
        raise _fail("batch.tx_per_batch", "має бути int у 8..12") from None
    if n < 8 or n > 12:
        raise _fail("batch.tx_per_batch", f"має бути у 8..12, отримано {n}")
    batch = BatchParams(
        tx_per_batch=n,
        cu_limit=int(b.get("cu_limit", 200_000)),
        cu_price_lamports=int(b.get("cu_price_lamports", 0)),
    )
    if batch.cu_limit <= 0 or batch.cu_price_lamports < 0:
        raise _fail("batch", "cu_limit > 0, cu_price_lamports >= 0")

    vlist = d.get("validators")
    if not isinstance(vlist, list) or not vlist:
        raise _fail("validators", "потрібен непорожній список (ціль ≥ 6 у проді)")
    validators = []
    for i, v in enumerate(vlist):
        if not isinstance(v, dict):
            raise _fail(f"validators[{i}]", "має бути мапою")
        for k in ("identity", "label", "expected_client"):
            if not v.get(k) or not isinstance(v[k], str):
                raise _fail(f"validators[{i}].{k}", "обов'язкове непорожнє string")
        validators.append(ValidatorRef(v["identity"], v["label"], v["expected_client"]))

    r = d.get("rpc", {}) or {}
    rpc = RpcRefs(
        http_url_ref=str(r.get("http_url_ref", "env:RPC_URL")),
        ws_url_ref=str(r.get("ws_url_ref", "env:WS_URL")),
    )
    for name, ref in (("rpc.http_url_ref", rpc.http_url_ref), ("rpc.ws_url_ref", rpc.ws_url_ref)):
        if not ref.startswith("env:"):
            raise _fail(name, f"лише посилання env:*, отримано {ref!r}; URL/секрети в YAML заборонені")

    return RunConfig(
        config_version=version,
        spend_cap_lamports=cap,
        base_fee_lamports=base_fee,
        batch=batch,
        validators=tuple(validators),
        rpc=rpc,
    )
