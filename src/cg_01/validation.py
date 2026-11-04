from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from .config import F1Config
from .models import Anomaly, DecisionSummary, Observation, RawCell, SourceInfo
from .text import clean_display_label, format_number, normalize_label, year_from_value


_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
_STATUS_ORDER = {
    "not_applicable": 0,
    "not_validated": 1,
    "validated": 2,
    "warning": 3,
    "invalid": 4,
}
_CONFLICT_ACCOUNTS = {
    "reservas",
    "total_corriente",
    "patrimonio_neto",
    "total_activo",
    "total_pasivo",
    "total_pasivo_patrimonio",
}


def _round(value: float) -> float:
    return round(value, 2)


def _alias_variant(text: str) -> str:
    value = text.casefold()
    value = re.sub(r"[^0-9a-záéíóúüñ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _set_status(observation: Observation, status: str, issue: str | None = None) -> None:
    if _STATUS_ORDER.get(status, 0) >= _STATUS_ORDER.get(observation.financial_status, 0):
        observation.financial_status = status
    if issue:
        observation.add_issue(issue)


def _provenance(observations: Iterable[Observation]) -> str:
    return " | ".join(
        f"{obs.source_id}:{obs.sheet}!{obs.cell}[{obs.period}]" for obs in observations
    )


def _raw_provenance(cells: Iterable[RawCell]) -> str:
    return " | ".join(
        f"{cell.source_id}:{cell.sheet}!{cell.coordinate}={cell.value!r}" for cell in cells
    )


@dataclass
class Validator:
    config: F1Config
    observations: list[Observation]
    summaries: list[DecisionSummary]
    sources: list[SourceInfo]
    raw_cells_by_source: dict[str, list[RawCell]]

    def __post_init__(self) -> None:
        self.numeric = [
            observation
            for observation in self.observations
            if observation.value_type == "number" and observation.numeric_value is not None
        ]
        self.anomalies: list[Anomaly] = []
        self._seen: set[tuple[str, str, str, str, str, str]] = set()

    def add(
        self,
        *,
        rule_id: str,
        severity: str,
        category: str,
        source_id: str,
        source_path: str,
        sheet: str,
        cell: str,
        period: str,
        message: str,
        expected: str = "",
        observed: str = "",
        difference: str = "",
        provenance: str = "",
    ) -> None:
        key = (rule_id, source_id, sheet, cell, period, message)
        if key in self._seen:
            return
        self._seen.add(key)
        self.anomalies.append(
            Anomaly(
                anomaly_id="",
                rule_id=rule_id,
                severity=severity,
                category=category,
                source_id=source_id,
                source_path=source_path,
                sheet=sheet,
                cell=cell,
                period=period,
                message=message,
                expected=expected,
                observed=observed,
                difference=difference,
                provenance=provenance,
            )
        )

    def _add_for_observation(
        self,
        observation: Observation,
        *,
        rule_id: str,
        severity: str,
        category: str,
        message: str,
        expected: str = "",
        observed: str = "",
        difference: str = "",
        provenance: str = "",
    ) -> None:
        self.add(
            rule_id=rule_id,
            severity=severity,
            category=category,
            source_id=observation.source_id,
            source_path=observation.source_path,
            sheet=observation.sheet,
            cell=observation.cell,
            period=observation.period,
            message=message,
            expected=expected,
            observed=observed,
            difference=difference,
            provenance=provenance or observation.provenance,
        )

    def check_prices(self) -> None:
        groups: dict[tuple[str, str, str, str], list[Observation]] = defaultdict(list)
        for observation in self.numeric:
            if not observation.period or "-Q" in observation.period:
                continue
            metric = normalize_label(observation.metric)
            label = observation.label_normalized
            if observation.source_type == "json":
                if "precio unitario" not in metric and "precio_unitario" not in observation.metric:
                    continue
                key = ("json", observation.scope, label)
            else:
                if (
                    "precio" not in label
                    and observation.unit != "EUR_per_unit"
                ) or observation.sheet not in {"Marketing", "Ventas"}:
                    continue
                key = (observation.source_id, observation.sheet, str(observation.block_id), label)
            groups[key].append(observation)

        for observations in groups.values():
            by_year: dict[int, Observation] = {}
            for observation in sorted(
                observations, key=lambda item: (item.year or 0, item.source_row, item.source_column)
            ):
                if observation.year is not None:
                    by_year.setdefault(observation.year, observation)
            years = sorted(by_year)
            for previous_year, current_year in zip(years, years[1:]):
                previous = by_year[previous_year]
                current = by_year[current_year]
                previous_value = previous.numeric_value
                current_value = current.numeric_value
                if previous_value is None or current_value is None or previous_value == 0:
                    continue
                change = (current_value - previous_value) / abs(previous_value) * 100.0
                if abs(change) > self.config.price_corridor_pct + 1e-9:
                    _set_status(current, "warning", f"precio fuera de ±{self.config.price_corridor_pct:g}%")
                    self._add_for_observation(
                        current,
                        rule_id="PRICE-CORRIDOR",
                        severity="high",
                        category="price",
                        message=(
                            f"Variación de precio de {change:.2f}% respecto a {previous.period}; "
                            f"supera el corredor ±{self.config.price_corridor_pct:g}%."
                        ),
                        expected=f"±{self.config.price_corridor_pct:g}%",
                        observed=f"{change:.2f}%",
                        difference=f"{abs(change) - self.config.price_corridor_pct:.2f} pp",
                        provenance=f"{previous.provenance} | {current.provenance}",
                    )
                else:
                    _set_status(previous, "validated")
                    _set_status(current, "validated")

    def check_production_semantics(self) -> None:
        for observation in self.numeric:
            label = observation.label_normalized
            metric = observation.metric
            is_production = (
                "unid producidas" in label
                or "unidades producir" in label
                or "unidades_producir" in metric
                or "unidades producir" in normalize_label(metric)
            )
            if not is_production:
                continue
            value = observation.numeric_value
            if value is None:
                continue
            if observation.data_type == "decision":
                if value == 0:
                    _set_status(observation, "validated")
                    self._add_for_observation(
                        observation,
                        rule_id="PROD-ZERO-KEEP",
                        severity="info",
                        category="semantics",
                        message=(
                            "Valor 0 en unidades a producir: significa mantener la producción "
                            "del periodo anterior (RG-02), no detener la planta."
                        ),
                        expected="0 = mantener",
                        observed="0",
                    )
                    continue
                if value == 1:
                    _set_status(observation, "validated")
                    self._add_for_observation(
                        observation,
                        rule_id="PROD-ONE-STOP",
                        severity="info",
                        category="semantics",
                        message="Valor 1 en unidades a producir: significa detener la producción (RG-02).",
                        expected="1 = detener",
                        observed="1",
                    )
                    continue
            if value < 0 or value > 600000:
                _set_status(observation, "invalid", "producción fuera de rango")
                self._add_for_observation(
                    observation,
                    rule_id="PROD-RANGE",
                    severity="high",
                    category="production",
                    message="Producción fuera del rango documentado 0..600.000 unidades.",
                    expected="0..600000",
                    observed=format_number(value),
                )
            else:
                _set_status(observation, "validated")

    def check_occupancy(self) -> None:
        threshold = self.config.occupancy_threshold_pct
        mode = self.config.occupancy_penalty_mode
        for observation in self.numeric:
            label = observation.label_normalized
            if "ocupacion" not in label and "tasa ocupa" not in label:
                continue
            if mode == "line":
                if normalize_label(observation.sheet) != "produccion":
                    continue
                if not observation.segment or year_from_value(observation.segment) is not None:
                    continue
                scope_label = f"línea {observation.segment}"
            else:
                if normalize_label(observation.sheet) == "produccion":
                    continue
                if "fabrica" not in label and "fabricas" not in label and "planta" not in label:
                    continue
                scope_label = "planta"
            value = observation.numeric_value
            if value is None:
                continue
            percentage = value * 100.0 if abs(value) <= 1.5 else value
            if percentage < threshold:
                _set_status(observation, "warning", "ocupación por debajo del mínimo")
                self._add_for_observation(
                    observation,
                    rule_id="OCCUPANCY-MIN",
                    severity="medium",
                    category="occupancy",
                    message=(
                        f"Ocupación de {scope_label} de {percentage:.2f}% por debajo del mínimo "
                        f"{threshold:g}% (occupancy_penalty_mode={mode})."
                    ),
                    expected=f">= {threshold:g}%",
                    observed=f"{percentage:.2f}%",
                    difference=f"{percentage - threshold:.2f} pp",
                )
            else:
                _set_status(observation, "validated")

    def _balance_groups(
        self, observations: list[Observation]
    ) -> dict[tuple[str, str, int | None, str, str], dict[str, list[Observation]]]:
        groups: dict[
            tuple[str, str, int | None, str, str], dict[str, list[Observation]]
        ] = defaultdict(lambda: defaultdict(list))
        for observation in observations:
            if (
                "balance" not in normalize_label(observation.sheet)
                and "balance" not in normalize_label(observation.scope)
            ):
                continue
            if observation.year is None or observation.value_type != "number":
                continue
            account = self.config.account(observation.label_raw)
            if not account:
                continue
            groups[
                (
                    observation.source_id,
                    observation.sheet,
                    observation.block_id,
                    observation.period,
                    observation.data_type,
                )
            ][account].append(observation)
        return groups

    def check_balance_identities(self) -> None:
        groups = self._balance_groups(self.observations)
        identities = [
            ("BAL-ASSETS-EQUATION", "total_activo", ["total_no_corriente", "total_corriente"], "critical"),
            ("BAL-ASSETS-LIAB-EQUITY", "total_activo", ["total_pasivo_patrimonio"], "critical"),
            ("BAL-CURRENT-ASSETS", "total_corriente", ["af_cp", "inventario", "cuentas_cobrar", "efectivo"], "high"),
            ("BAL-EQUITY", "patrimonio_neto", ["capital", "reservas", "resultado"], "high"),
            ("BAL-LIABILITIES", "total_pasivo", ["total_pasivo_corriente", "prestamo_lp", "credito_extra"], "high"),
            ("BAL-CURRENT-LIABILITIES", "total_pasivo_corriente", ["prestamo_cp", "credito_extra", "proveedores", "impuestos?"], "high"),
            ("BAL-LIAB-EQUITY", "total_pasivo_patrimonio", ["total_pasivo", "patrimonio_neto"], "high"),
        ]
        for (source_id, sheet, block_id, period, data_type), accounts in groups.items():
            for rule_id, total_account, component_accounts, severity in identities:
                total_obs_list = accounts.get(total_account, [])
                if not total_obs_list:
                    continue
                total_observation = sorted(total_obs_list, key=lambda item: item.source_row)[0]
                component_observations: list[Observation] = []
                expected = 0.0
                missing = False
                for account in component_accounts:
                    optional = account.endswith("?")
                    account_name = account.rstrip("?")
                    candidates = accounts.get(account_name, [])
                    if not candidates:
                        if optional:
                            continue
                        missing = True
                        break
                    observation = sorted(candidates, key=lambda item: item.source_row)[0]
                    value = observation.numeric_value
                    if value is None:
                        if optional:
                            continue
                        missing = True
                        break
                    expected += value
                    component_observations.append(observation)
                if missing:
                    continue
                observed = total_observation.numeric_value
                if observed is None:
                    continue
                difference = observed - expected
                if abs(difference) <= self.config.balance_tolerance_eur:
                    _set_status(total_observation, "validated")
                    for observation in component_observations:
                        _set_status(observation, "validated")
                    continue
                status = "invalid" if severity == "critical" else "warning"
                _set_status(total_observation, status, "identidad contable no cuadra")
                for observation in component_observations:
                    _set_status(observation, status, "identidad contable no cuadra")
                formula = " + ".join(account.rstrip("?") for account in component_accounts)
                self._add_for_observation(
                    total_observation,
                    rule_id=rule_id,
                    severity=severity,
                    category="balance",
                    message=f"La identidad contable no cuadra: {total_account} != {formula}.",
                    expected=format_number(_round(expected)),
                    observed=format_number(_round(observed)),
                    difference=format_number(_round(difference)),
                    provenance=_provenance([total_observation, *component_observations]),
                )

    def check_cross_block_conflicts(self) -> None:
        groups: dict[tuple[str, str, str, str], list[Observation]] = defaultdict(list)
        for observation in self.numeric:
            if observation.year is None or "balance" not in normalize_label(observation.sheet):
                continue
            account = self.config.account(observation.label_raw)
            if account not in _CONFLICT_ACCOUNTS:
                continue
            groups[(observation.source_id, observation.sheet, observation.period, account)].append(observation)

        for (source_id, sheet, period, account), observations in groups.items():
            values = {
                _round(observation.numeric_value)
                for observation in observations
                if observation.numeric_value is not None
            }
            if len(values) <= 1:
                continue
            ordered = sorted(observations, key=lambda item: item.source_row)
            if max(values) - min(values) <= self.config.balance_tolerance_eur:
                continue
            for observation in ordered:
                _set_status(observation, "warning", "valor distinto para la misma cuenta y periodo")
            first = ordered[0]
            self._add_for_observation(
                first,
                rule_id="BAL-CROSS-BLOCK",
                severity="high",
                category="balance",
                message=(
                    f"La cuenta '{account}' tiene valores distintos en bloques del mismo periodo: "
                    f"{', '.join(format_number(value) for value in sorted(values))}."
                ),
                expected="un único valor por cuenta y periodo",
                observed="; ".join(f"{obs.cell}={format_number(obs.numeric_value)}" for obs in ordered),
                difference=format_number(_round(max(values) - min(values))),
                provenance=_provenance(ordered),
            )

    def check_scale_mismatch(self) -> None:
        groups: dict[tuple[str, str, str], list[Observation]] = defaultdict(list)
        for observation in self.numeric:
            if observation.year is None or "total" not in observation.label_normalized:
                continue
            value = observation.numeric_value
            if value is None or abs(value) <= 1000:
                continue
            groups[(observation.source_id, observation.sheet, observation.period)].append(observation)

        for (source_id, sheet, period), observations in groups.items():
            ordered = sorted(observations, key=lambda item: item.source_row)
            for index, first in enumerate(ordered):
                for second in ordered[index + 1 :]:
                    first_value = first.numeric_value
                    second_value = second.numeric_value
                    if first_value is None or second_value is None:
                        continue
                    ratio = max(abs(first_value), abs(second_value)) / min(abs(first_value), abs(second_value))
                    if abs(ratio - 100.0) <= 1.0:
                        _set_status(first, "warning", "posible error de escala ×100")
                        _set_status(second, "warning", "posible error de escala ×100")
                        smaller = min((first, second), key=lambda item: abs(item.numeric_value or 0.0))
                        if (
                            smaller.normalized_value is not None
                            and smaller.normalization_status != "pending_scale_confirmation"
                        ):
                            smaller.normalized_value = smaller.normalized_value * 100.0
                            smaller.normalization_status = "pending_scale_confirmation"
                            smaller.normalization_note = (
                                "valor bruto conservado en 'value'; normalización ×100 inferida por las tablas, "
                                "pendiente de confirmación explícita"
                            )
                        self._add_for_observation(
                            first,
                            rule_id="SCALE-100",
                            severity="high",
                            category="scale",
                            message=(
                                "Dos totales del mismo periodo difieren en un factor ~100; "
                                "posible error de escala."
                            ),
                            expected="misma escala",
                            observed=f"factor {ratio:.2f}",
                            difference=f"{format_number(first_value)} vs {format_number(second_value)}",
                            provenance=f"{first.provenance} | {second.provenance}",
                        )

    def check_general_expenses(self) -> None:
        groups: dict[tuple[str, str, str], dict[str, Observation]] = defaultdict(dict)
        for observation in self.numeric:
            if normalize_label(observation.sheet) != "resultados" or observation.year is None:
                continue
            label = observation.label_normalized
            if label == "gastos generales":
                groups[(observation.source_id, observation.sheet, observation.period)]["total"] = observation
            elif label == "procesos administrativos":
                groups[(observation.source_id, observation.sheet, observation.period)]["detail"] = observation
        for (source_id, sheet, period), pair in groups.items():
            total = pair.get("total")
            detail = pair.get("detail")
            if total is None or detail is None:
                continue
            total_value = total.numeric_value
            detail_value = detail.numeric_value
            if total_value is None or detail_value is None:
                continue
            difference = total_value - detail_value
            if abs(difference) <= self.config.balance_tolerance_eur:
                _set_status(total, "validated")
                _set_status(detail, "validated")
                continue
            _set_status(total, "warning", "gastos generales no coinciden con el detalle")
            _set_status(detail, "warning", "detalle de gastos generales no coincide con el total")
            self._add_for_observation(
                total,
                rule_id="EXPENSE-GENERAL",
                severity="high",
                category="expense",
                message="El total de gastos generales no coincide con el detalle administrativo.",
                expected=format_number(_round(detail_value)),
                observed=format_number(_round(total_value)),
                difference=format_number(_round(difference)),
                provenance=f"{total.provenance} | {detail.provenance}",
            )

    def _summary_for(self, period: int) -> list[DecisionSummary]:
        return [summary for summary in self.summaries if summary.period == period]

    def check_decision_cross_source(self) -> None:
        seen_capex: set[tuple[str, str, int]] = set()
        for summary in self.summaries:
            if not summary.period:
                continue
            period = str(summary.period)
            if summary.capex_selected:
                by_block: dict[tuple[str, str, int | None], dict[int, Observation]] = defaultdict(dict)
                for observation in self.numeric:
                    if (
                        observation.year is None
                        or normalize_label(observation.sheet) != "analisis de balance"
                        or "inmovilizado material bruto" not in observation.label_normalized
                    ):
                        continue
                    by_block[(observation.source_id, observation.sheet, observation.block_id)][
                        observation.year
                    ] = observation
                for key, by_year in by_block.items():
                    if summary.period not in by_year or summary.period - 1 not in by_year:
                        continue
                    current = by_year[summary.period]
                    capex_key = (current.source_id, current.sheet, summary.period)
                    if capex_key in seen_capex:
                        continue
                    previous = by_year[summary.period - 1]
                    current_value = current.numeric_value
                    previous_value = previous.numeric_value
                    if current_value is None or previous_value is None:
                        continue
                    delta = current_value - previous_value
                    difference = delta - summary.capex_selected
                    if abs(difference) <= max(self.config.balance_tolerance_eur, abs(delta) * 0.01):
                        continue
                    seen_capex.add(capex_key)
                    self._add_for_observation(
                        current,
                        rule_id="CAPEX-CROSS",
                        severity="high",
                        category="capex",
                        message=(
                            "El incremento de inmovilizado material no coincide con la suma de "
                            "inversiones seleccionadas de la bitácora."
                        ),
                        expected=format_number(_round(summary.capex_selected)),
                        observed=format_number(_round(delta)),
                        difference=format_number(_round(difference)),
                        provenance=f"{previous.provenance} | {current.provenance}",
                    )

            if summary.maintenance_pct is not None:
                asset = next(
                    (
                        observation
                        for observation in self.numeric
                        if observation.year == summary.period
                        and normalize_label(observation.sheet) == "produccion"
                        and observation.label_normalized == "activo fabrica"
                    ),
                    None,
                )
                maintenance = next(
                    (
                        observation
                        for observation in self.numeric
                        if observation.year == summary.period
                        and normalize_label(observation.sheet) == "resultados"
                        and observation.label_normalized == "gastos mantenimiento"
                    ),
                    None,
                )
                if asset is not None and maintenance is not None:
                    asset_value = asset.numeric_value
                    maintenance_value = maintenance.numeric_value
                    if asset_value and maintenance_value is not None:
                        calculated = maintenance_value / asset_value * 100.0
                        difference = calculated - summary.maintenance_pct
                        if abs(difference) > 0.01:
                            _set_status(maintenance, "warning", "porcentaje de mantenimiento no coincide")
                            self._add_for_observation(
                                maintenance,
                                rule_id="MAINTENANCE-CROSS",
                                severity="medium",
                                category="maintenance",
                                message="El gasto de mantenimiento no coincide con el porcentaje de la bitácora.",
                                expected=f"{summary.maintenance_pct:g}%",
                                observed=f"{calculated:.2f}%",
                                difference=f"{difference:.2f} pp",
                                provenance=f"{asset.provenance} | {maintenance.provenance}",
                            )
                        else:
                            _set_status(maintenance, "validated")

            for product, decision_value in summary.prices.items():
                candidates = [
                    observation
                    for observation in self.numeric
                    if observation.year == summary.period
                    and normalize_label(observation.sheet) == "marketing"
                    and observation.label_normalized == normalize_label(product)
                    and observation.unit == "EUR_per_unit"
                ]
                if not candidates:
                    continue
                block_id = min(
                    (observation.block_id for observation in candidates if observation.block_id is not None),
                    default=None,
                )
                candidates = [
                    observation for observation in candidates if observation.block_id == block_id
                ]
                if not candidates:
                    continue
                excel = sorted(candidates, key=lambda item: item.source_row)[0]
                excel_value = excel.numeric_value
                if excel_value is None:
                    continue
                difference = decision_value - excel_value
                if abs(difference) > 0.01:
                    self.add(
                        rule_id="PRICE-CROSS",
                        severity="high",
                        category="price",
                        source_id=excel.source_id,
                        source_path=excel.source_path,
                        sheet=excel.sheet,
                        cell=excel.cell,
                        period=period,
                        message=f"El precio de {product} en la bitácora no coincide con Marketing.",
                        expected=format_number(_round(excel_value)),
                        observed=format_number(_round(decision_value)),
                        difference=format_number(_round(difference)),
                        provenance=excel.provenance,
                    )

            for product, decision_value in summary.production_units.items():
                candidates = [
                    observation
                    for observation in self.numeric
                    if observation.year == summary.period
                    and normalize_label(observation.sheet) == "produccion"
                    and "unid producidas" in observation.label_normalized
                    and normalize_label(observation.segment) == normalize_label(product)
                ]
                if not candidates:
                    continue
                excel = sorted(candidates, key=lambda item: item.source_row)[0]
                excel_value = excel.numeric_value
                if excel_value is None:
                    continue
                difference = decision_value - excel_value
                if abs(difference) > 0.5:
                    self.add(
                        rule_id="PRODUCTION-CROSS",
                        severity="medium",
                        category="production",
                        source_id=excel.source_id,
                        source_path=excel.source_path,
                        sheet=excel.sheet,
                        cell=excel.cell,
                        period=period,
                        message=f"Las unidades a producir de {product} no coinciden con Producción.",
                        expected=format_number(_round(excel_value)),
                        observed=format_number(_round(decision_value)),
                        difference=format_number(_round(difference)),
                        provenance=excel.provenance,
                    )

    def check_aliases(self) -> None:
        variants: dict[str, dict[str, list[RawCell]]] = defaultdict(lambda: defaultdict(list))
        for cells in self.raw_cells_by_source.values():
            for cell in cells:
                if cell.value_type != "string":
                    continue
                text = clean_display_label(cell.value)
                if len(text) < 3 or len(text) > 40 or "\n" in text:
                    continue
                if " " in text:
                    continue
                if year_from_value(text) is not None:
                    continue
                normalized = normalize_label(text)
                if len(normalized) < 3 or normalized.isdigit():
                    continue
                variant = _alias_variant(text)
                if variant:
                    variants[normalized][variant].append(cell)
        for normalized, by_variant in variants.items():
            if len(by_variant) <= 1:
                continue
            first_cells = [cells[0] for cells in by_variant.values()]
            first = first_cells[0]
            labels = ", ".join(sorted(by_variant))
            self.add(
                rule_id="ALIAS-TEXT",
                severity="low",
                category="alias",
                source_id=first.source_id,
                source_path=first.source_path,
                sheet=first.sheet,
                cell=first.coordinate,
                period="",
                message=f"Variantes de escritura para el mismo valor normalizado '{normalized}': {labels}.",
                expected="una única forma de escritura",
                observed=labels,
                provenance=_raw_provenance(cell for cells in by_variant.values() for cell in cells),
            )

    def run(self) -> list[Anomaly]:
        self.check_prices()
        self.check_production_semantics()
        self.check_occupancy()
        self.check_balance_identities()
        self.check_cross_block_conflicts()
        self.check_scale_mismatch()
        self.check_general_expenses()
        self.check_decision_cross_source()
        self.check_aliases()
        self.anomalies.sort(
            key=lambda anomaly: (
                _SEVERITY_ORDER.get(anomaly.severity, 99),
                anomaly.rule_id,
                anomaly.source_id,
                anomaly.sheet,
                anomaly.cell,
                anomaly.period,
            )
        )
        for index, anomaly in enumerate(self.anomalies, start=1):
            anomaly.anomaly_id = f"ANOM-{index:04d}"
        return self.anomalies


def validate_observations(
    observations: list[Observation],
    summaries: list[DecisionSummary],
    sources: list[SourceInfo],
    raw_cells_by_source: dict[str, list[RawCell]],
    config: F1Config,
) -> list[Anomaly]:
    return Validator(
        config=config,
        observations=observations,
        summaries=summaries,
        sources=sources,
        raw_cells_by_source=raw_cells_by_source,
    ).run()
