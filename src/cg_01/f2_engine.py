from __future__ import annotations

import argparse
import json
import tomllib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .config import F1Config, PROJECT_ROOT, load_config
from .models import Anomaly, Observation
from .pipeline import PipelineResult, run_pipeline
from .text import normalize_label


STATUS_ORDER = {
    "confirmed": 0,
    "inferred_accepted": 1,
    "accepted_exception": 2,
    "pending": 3,
    "unreconciled": 4,
}
RECONCILIATION_ORDER = {
    "not_applicable": 0,
    "exact": 1,
    "documented_residual": 2,
    "unreconciled": 3,
}
PRODUCTS = ("Corbatas", "Bufandas", "Calcetines")
BALANCE_TOTAL_LABELS = {
    "total activo",
    "activo total",
    "total pasivo",
    "total pasivo patrimonio neto",
    "patrimonio neto",
    "patrimonio neto pasivo",
    "reservas",
    "total corriente",
    "total pasivo corriente",
}


@dataclass(frozen=True)
class F2Config:
    project_root: Path
    output_dir: Path
    exact_tolerance_eur: float = 0.005
    documented_residual_eur: float = 1.0


@dataclass
class F2Row:
    section: str
    metric: str
    period: int
    value: float | None
    unit: str
    status: str
    source_anomaly_status: str
    reconciliation_status: str
    tolerance_eur: float
    source_primary: str
    source_cells: str
    pd_dependencies: str
    derived_from: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "section": self.section,
            "metric": self.metric,
            "period": self.period,
            "value": self.value,
            "unit": self.unit,
            "status": self.status,
            "source_anomaly_status": self.source_anomaly_status,
            "reconciliation_status": self.reconciliation_status,
            "tolerance_eur": self.tolerance_eur,
            "source_primary": self.source_primary,
            "source_cells": self.source_cells,
            "pd_dependencies": self.pd_dependencies,
            "derived_from": self.derived_from,
            "notes": self.notes,
        }


@dataclass
class F2Result:
    f1_config: F1Config
    f2_config: F2Config
    pipeline: PipelineResult
    rows: list[F2Row]
    balance_anomalies: list[dict[str, Any]]
    manifest: dict[str, Any] = field(default_factory=dict)


def load_f2_config(
    path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    project_root: str | Path | None = None,
) -> F2Config:
    config_path = Path(path) if path is not None else PROJECT_ROOT / "config" / "f2.toml"
    root = Path(project_root) if project_root is not None else config_path.parent.parent
    raw: dict[str, Any] = {}
    if config_path.exists():
        with config_path.open("rb") as handle:
            raw = tomllib.load(handle)
    paths = raw.get("paths", {}) if isinstance(raw.get("paths", {}), dict) else {}
    reconciliation = raw.get("reconciliation", {}) if isinstance(raw.get("reconciliation", {}), dict) else {}
    resolved_output = Path(output_dir) if output_dir is not None else Path(str(paths.get("output_dir", "outputs/f2")))
    if not resolved_output.is_absolute():
        resolved_output = (root / resolved_output).resolve()
    return F2Config(
        project_root=root,
        output_dir=resolved_output,
        exact_tolerance_eur=float(reconciliation.get("exact_tolerance_eur", 0.005)),
        documented_residual_eur=float(reconciliation.get("documented_residual_eur", 1.0)),
    )


def _sheet_key(sheet: str) -> str:
    value = normalize_label(sheet)
    value = value.replace("analisis de ", "").replace("analisis ", "")
    value = value.replace("valor de ", "valor ")
    return value


def _source(observation: Observation | None) -> str:
    return observation.source_id if observation is not None else ""


def _cells(observations: Iterable[Observation | None]) -> str:
    return " | ".join(
        f"{obs.source_id}:{obs.sheet}!{obs.cell}[{obs.period}]"
        for obs in observations
        if obs is not None
    )


def _status(*statuses: str) -> str:
    return max(statuses, key=lambda value: STATUS_ORDER.get(value, 99))


def _reconciliation(*statuses: str) -> str:
    return max(statuses, key=lambda value: RECONCILIATION_ORDER.get(value, 99))


def _within(value: float | None, tolerance: float) -> bool:
    return value is not None and abs(value) <= tolerance + 1e-9


class Builder:
    def __init__(self, pipeline: PipelineResult, config: F2Config) -> None:
        self.pipeline = pipeline
        self.config = config
        self.rows: list[F2Row] = []
        self.observations = pipeline.observations
        self.obs_by_cell = {
            (obs.source_id, obs.sheet, obs.cell, obs.period): obs for obs in self.observations
        }
        self.balance_anomalies = [
            anomaly for anomaly in pipeline.anomalies if anomaly.category == "balance"
        ]
        self.balance_labels: set[tuple[str, str]] = set()
        for anomaly in self.balance_anomalies:
            observation = self.obs_by_cell.get(
                (anomaly.source_id, anomaly.sheet, anomaly.cell, anomaly.period)
            )
            if observation is not None:
                self.balance_labels.add((observation.period, observation.label_normalized))

    def find(
        self,
        period: int,
        sheet: str,
        label: str,
        *,
        scope_contains: str | None = None,
    ) -> Observation | None:
        target_label = normalize_label(label)
        target_sheet = _sheet_key(sheet)
        target_scope = normalize_label(scope_contains) if scope_contains else ""
        candidates = []
        for observation in self.observations:
            if observation.year != period or observation.data_type != "real":
                continue
            if _sheet_key(observation.sheet) != target_sheet:
                continue
            if observation.label_normalized != target_label:
                continue
            if target_scope and target_scope not in normalize_label(observation.scope):
                continue
            candidates.append(observation)
        if not candidates:
            return None
        priority = {
            2027: {"SRC-XLSX-003": 0},
            2026: {"SRC-XLSX-003": 0, "SRC-XLSX-002": 1, "SRC-XLSX-001": 2},
            2025: {"SRC-XLSX-003": 0, "SRC-XLSX-002": 1, "SRC-XLSX-001": 2},
            2024: {"SRC-XLSX-003": 0, "SRC-XLSX-002": 1, "SRC-XLSX-001": 2},
        }.get(period, {})
        return min(
            candidates,
            key=lambda obs: (
                priority.get(obs.source_id, 9),
                obs.source_row,
                obs.source_column,
            ),
        )

    def value(self, period: int, sheet: str, label: str, *, scope_contains: str | None = None) -> float | None:
        observation = self.find(period, sheet, label, scope_contains=scope_contains)
        return observation.numeric_value if observation is not None else None

    def balance_value(self, period: int, label: str) -> float | None:
        return self.value(period, "Balance", label, scope_contains="Balance de Situación")

    def balance_obs(self, period: int, label: str) -> Observation | None:
        return self.find(period, "Balance", label, scope_contains="Balance de Situación")

    def debt_value(self, period: int, label: str) -> float | None:
        return self.value(period, "Balance", label, scope_contains="Análisis de los gastos financieros")

    def debt_obs(self, period: int, label: str) -> Observation | None:
        return self.find(period, "Balance", label, scope_contains="Análisis de los gastos financieros")

    def product_value(self, period: int, product: str, label: str) -> float | None:
        return self.value(period, "Margen", label, scope_contains=f"Análisis Margen Producto {product}")

    def product_obs(self, period: int, product: str, label: str) -> Observation | None:
        return self.find(period, "Margen", label, scope_contains=f"Análisis Margen Producto {product}")

    def balance_unreconciled(self, period: int, label: str) -> bool:
        return (str(period), normalize_label(label)) in self.balance_labels or (
            period in {2026, 2027} and normalize_label(label) in BALANCE_TOTAL_LABELS
        )

    def add(
        self,
        *,
        section: str,
        metric: str,
        period: int,
        value: float | None,
        unit: str = "EUR",
        status: str = "confirmed",
        source: Observation | None = None,
        sources: Iterable[Observation | None] = (),
        pd_dependencies: str = "",
        derived_from: str = "",
        notes: str = "",
        reconciliation_status: str = "exact",
        tolerance_eur: float | None = None,
        source_unreconciled: bool = False,
        source_cells_override: str | None = None,
    ) -> F2Row:
        if value is None:
            status = _status(status, "pending")
            reconciliation_status = "not_applicable"
        if source_unreconciled:
            status = "unreconciled"
        effective_tolerance = (
            tolerance_eur
            if tolerance_eur is not None
            else (self.config.documented_residual_eur if unit == "EUR" else 0.0)
        )
        row = F2Row(
            section=section,
            metric=metric,
            period=period,
            value=value,
            unit=unit,
            status=status,
            source_anomaly_status="unreconciled" if source_unreconciled else "not_applicable",
            reconciliation_status=reconciliation_status,
            tolerance_eur=effective_tolerance,
            source_primary=_source(source),
            source_cells=source_cells_override or _cells([source, *sources]),
            pd_dependencies=pd_dependencies,
            derived_from=derived_from,
            notes=notes,
        )
        self.rows.append(row)
        return row

    def build_income_statement(self, period: int) -> None:
        revenue = self.find(period, "Resultados", "Ingresos Totales")
        cost = self.find(period, "Resultados", "Total Coste de las Ventas")
        gross = self.find(period, "Resultados", "Margen")
        marketing = self.find(period, "Resultados", "Gastos de Marketing")
        personnel = self.find(period, "Resultados", "Gastos de Personal")
        rd = self.find(period, "Resultados", "Gastos I+D")
        depreciation = self.find(period, "Resultados", "Gastos de Depreciación")
        insolvency = self.find(period, "Resultados", "Dotaciones por Insolvencias")
        general = self.find(period, "Resultados", "Gastos Generales")
        operating_total = self.find(period, "Resultados", "Total Gastos Operación")
        gross_result = self.find(period, "Resultados", "Resultado Bruto")
        financial_income = self.find(period, "Resultados", "Ingresos Financieros")
        financial_expense = self.find(period, "Resultados", "Gastos Financieros")
        financial_result = self.find(period, "Resultados", "Resultado Financiero")
        extraordinary = self.find(period, "Resultados", "Resultados Extraordinarios")
        net_before = self.find(period, "Resultados", "Resultado Neto")
        taxes = self.find(period, "Resultados", "Impuestos")
        net_after = self.find(period, "Resultados", "Resultado Desp. Impuestos")

        revenue_status = "inferred_accepted"
        general_status = "pending" if period == 2026 else "confirmed"
        operating_status = _status("inferred_accepted", general_status)
        net_status = operating_status

        self.add(
            section="income_statement",
            metric="revenue_total",
            period=period,
            value=revenue.numeric_value if revenue else None,
            source=revenue,
            status=revenue_status,
            pd_dependencies="PD-05",
            notes="Se usa el valor normalizado 3.861.039/4.304.333; la fila de total bruta es 38.610,39/43.043,325 (INT-003).",
        )
        self.add(
            section="income_statement",
            metric="cost_of_sales_total",
            period=period,
            value=cost.numeric_value if cost else None,
            source=cost,
        )
        self.add(
            section="income_statement",
            metric="gross_profit",
            period=period,
            value=gross.numeric_value if gross else None,
            source=gross,
            status=revenue_status,
            derived_from="revenue_total - cost_of_sales_total",
            pd_dependencies="PD-05",
            reconciliation_status="exact",
            notes="Derivado de ingresos y coste de ventas.",
        )
        for metric, observation, metric_status, pd in (
            ("marketing_expenses", marketing, "confirmed", ""),
            ("personnel_expenses", personnel, "confirmed", ""),
            ("rd_expenses", rd, "confirmed", ""),
            ("depreciation_expenses", depreciation, "confirmed", ""),
            ("insolvency_expenses", insolvency, "confirmed", ""),
            ("general_expenses", general, general_status, "PD-06" if period == 2026 else ""),
            ("operating_expenses_total", operating_total, operating_status, "PD-06" if period == 2026 else ""),
        ):
            note = ""
            if metric == "general_expenses" and period == 2026:
                note = "Total 344.808; detalle 194.808. Los 150.000 son hipótesis del usuario (INT-009)."
            self.add(
                section="income_statement",
                metric=metric,
                period=period,
                value=observation.numeric_value if observation else None,
                source=observation,
                status=metric_status,
                pd_dependencies=pd,
                notes=note,
            )
        self.add(
            section="income_statement",
            metric="gross_result",
            period=period,
            value=gross_result.numeric_value if gross_result else None,
            source=gross_result,
            status=net_status,
            derived_from="gross_profit - operating_expenses_total",
            pd_dependencies="PD-05" + (",PD-06" if period == 2026 else ""),
            notes="Derivado; hereda el estado de ingresos y gastos generales.",
        )
        for metric, observation in (
            ("financial_income", financial_income),
            ("financial_expense", financial_expense),
            ("financial_result", financial_result),
            ("extraordinary_result", extraordinary),
            ("taxes", taxes),
        ):
            self.add(
                section="income_statement",
                metric=metric,
                period=period,
                value=observation.numeric_value if observation else None,
                source=observation,
            )
        self.add(
            section="income_statement",
            metric="net_result_before_taxes",
            period=period,
            value=net_before.numeric_value if net_before else None,
            source=net_before,
            status=net_status,
            derived_from="gross_result + financial_result + extraordinary_result",
            pd_dependencies="PD-05" + (",PD-06" if period == 2026 else ""),
        )
        self.add(
            section="income_statement",
            metric="net_result_after_taxes",
            period=period,
            value=net_after.numeric_value if net_after else None,
            source=net_after,
            status=net_status,
            derived_from="net_result_before_taxes - taxes",
            pd_dependencies="PD-05" + (",PD-06" if period == 2026 else ""),
        )
        if revenue and revenue.numeric_value:
            self.add(
                section="income_statement",
                metric="gross_margin_pct",
                period=period,
                value=(gross.numeric_value / revenue.numeric_value) if gross and gross.numeric_value is not None else None,
                unit="percent",
                status=revenue_status,
                source=gross,
                derived_from="gross_profit / revenue_total",
                pd_dependencies="PD-05",
                reconciliation_status="not_applicable",
                tolerance_eur=0.0,
            )
            self.add(
                section="income_statement",
                metric="net_margin_pct",
                period=period,
                value=(net_after.numeric_value / revenue.numeric_value) if net_after and net_after.numeric_value is not None else None,
                unit="percent",
                status=net_status,
                source=net_after,
                derived_from="net_result_after_taxes / revenue_total",
                pd_dependencies="PD-05" + (",PD-06" if period == 2026 else ""),
                reconciliation_status="not_applicable",
                tolerance_eur=0.0,
            )

        for product in PRODUCTS:
            revenue_obs = self.product_obs(period, product, "Ingresos Totales")
            cost_obs = self.product_obs(period, product, "Total Coste de las Ventas")
            margin_obs = self.product_obs(period, product, "Margen")
            self.add(
                section="income_statement",
                metric=f"revenue_{product.lower()}",
                period=period,
                value=revenue_obs.numeric_value if revenue_obs else None,
                source=revenue_obs,
                notes=f"Producto {product}.",
            )
            self.add(
                section="income_statement",
                metric=f"cost_{product.lower()}",
                period=period,
                value=cost_obs.numeric_value if cost_obs else None,
                source=cost_obs,
                notes=f"Producto {product}.",
            )
            self.add(
                section="income_statement",
                metric=f"margin_{product.lower()}",
                period=period,
                value=margin_obs.numeric_value if margin_obs else None,
                source=margin_obs,
                derived_from=f"revenue_{product.lower()} - cost_{product.lower()}",
                notes=f"Producto {product}; margen directo de fuente.",
            )

    def build_balance(self, period: int) -> None:
        labels = [
            ("total_non_current_assets", "total no corriente", "confirmed"),
            ("financial_assets_cp", "activos financieros a cp", "confirmed"),
            ("inventory", "inventario", "confirmed"),
            ("accounts_receivable", "cuentas por cobrar neto", "confirmed"),
            ("cash", "efectivo disponible", "confirmed"),
            ("total_current_assets", "total corriente", "unreconciled"),
            ("total_assets", "activo total", "unreconciled"),
            ("capital", "capital", "confirmed"),
            ("reserves", "reservas", "unreconciled"),
            ("result", "resultado desp impuestos", "pending" if period == 2026 else "inferred_accepted"),
            ("reported_equity", "patrimonio neto", "unreconciled"),
            ("long_term_debt", "prestamo largo plazo", "confirmed"),
            ("short_term_debt", "prestamo corto plazo", "confirmed"),
            ("extraordinary_debt", "credito extraordinario", "confirmed"),
            ("taxes_payable", "impuestos pendientes de pago", "confirmed"),
            ("suppliers", "proveedores", "confirmed"),
            ("total_current_liabilities", "total pasivo corriente", "unreconciled"),
            ("total_liabilities", "total pasivo", "unreconciled"),
            ("total_liabilities_equity", "patrimonio neto pasivo", "unreconciled"),
        ]
        values: dict[str, Observation | None] = {}
        for metric, label, metric_status in labels:
            observation = self.balance_obs(period, label)
            values[metric] = observation
            if metric == "current_portion_lp":
                continue
            source_unreconciled = self.balance_unreconciled(period, label)
            self.add(
                section="balance",
                metric=metric,
                period=period,
                value=observation.numeric_value if observation else None,
                source=observation,
                status=metric_status,
                source_unreconciled=source_unreconciled,
                pd_dependencies="PD-06" if metric == "result" and period == 2026 else "",
                notes="Reservas detalladas; el resumen 1.177.053/1.332.003 no se usa en la identidad." if metric == "reserves" else "",
            )

        capital = values["capital"].numeric_value if values["capital"] else None
        reserves = values["reserves"].numeric_value if values["reserves"] else None
        result = values["result"].numeric_value if values["result"] else None
        detailed_equity = (
            capital + reserves + result
            if capital is not None and reserves is not None and result is not None
            else None
        )
        liabilities = values["total_liabilities"].numeric_value if values["total_liabilities"] else None
        assets = values["total_assets"].numeric_value if values["total_assets"] else None
        reported_equity = values["reported_equity"].numeric_value if values["reported_equity"] else None
        detailed_identity = (
            assets - (liabilities + detailed_equity)
            if assets is not None and liabilities is not None and detailed_equity is not None
            else None
        )
        reported_identity = (
            assets - (liabilities + reported_equity)
            if assets is not None and liabilities is not None and reported_equity is not None
            else None
        )
        self.add(
            section="balance",
            metric="detailed_equity",
            period=period,
            value=detailed_equity,
            sources=[values["capital"], values["reserves"], values["result"]],
            status="unreconciled",
            source_unreconciled=True,
            derived_from="capital + reserves_detailed + result",
            notes="Patrimonio detallado; no se usa el patrimonio reportado.",
            reconciliation_status="documented_residual" if _within(detailed_identity, 1.0) else "unreconciled",
        )
        self.add(
            section="balance",
            metric="balance_detail_residual",
            period=period,
            value=detailed_identity,
            sources=[values["total_assets"], values["total_liabilities"]],
            status="unreconciled",
            source_unreconciled=True,
            derived_from="total_assets - (total_liabilities + detailed_equity)",
            reconciliation_status="documented_residual" if _within(detailed_identity, 1.0) else "unreconciled",
            notes="Residual de 1 € documentado; no se redondea ni se corrige la fuente.",
        )
        self.add(
            section="balance",
            metric="balance_reported_residual",
            period=period,
            value=reported_identity,
            sources=[values["total_assets"], values["total_liabilities"], values["reported_equity"]],
            status="unreconciled",
            source_unreconciled=True,
            derived_from="total_assets - (total_liabilities + reported_equity)",
            reconciliation_status="documented_residual" if _within(reported_identity, 1.0) else "unreconciled",
            notes="El patrimonio reportado no concilia con el bloque detallado.",
        )

        current_assets = values["total_current_assets"].numeric_value if values["total_current_assets"] else None
        current_liabilities = values["total_current_liabilities"].numeric_value if values["total_current_liabilities"] else None
        current_ratio = (
            current_assets / current_liabilities
            if current_assets is not None and current_liabilities not in (None, 0)
            else None
        )
        working_capital = (
            current_assets - current_liabilities
            if current_assets is not None and current_liabilities is not None
            else None
        )
        self.add(
            section="balance",
            metric="current_ratio",
            period=period,
            value=current_ratio,
            unit="ratio",
            status="unreconciled",
            sources=[values["total_current_assets"], values["total_current_liabilities"]],
            source_unreconciled=True,
            derived_from="total_current_assets / total_current_liabilities",
            reconciliation_status="not_applicable",
            tolerance_eur=0.0,
        )
        self.add(
            section="balance",
            metric="working_capital",
            period=period,
            value=working_capital,
            status="unreconciled",
            sources=[values["total_current_assets"], values["total_current_liabilities"]],
            source_unreconciled=True,
            derived_from="total_current_assets - total_current_liabilities",
            reconciliation_status="not_applicable",
        )

    def build_debt(self, period: int) -> None:
        lp = self.debt_obs(period, "Pendiente Préstamo LP")
        cp_direct = self.debt_obs(period, "Saldo Préstamo CP")
        current_portion = self.debt_obs(period, "Saldo CP procedente del LP")
        extraordinary = self.debt_obs(period, "Crédito Extraordinario CP")
        total = self.debt_obs(period, "Total Deuda Bancaria")
        interest = self.debt_obs(period, "Total Gastos Intereses")
        for metric, observation, note in (
            ("long_term_debt", lp, "LP pendiente."),
            ("short_term_debt_direct", cp_direct, "Saldo CP directo."),
            ("current_portion_long_term_debt", current_portion, "Porción corriente del LP."),
            ("extraordinary_debt", extraordinary, "Crédito extraordinario."),
            ("total_debt", total, "Total deuda bancaria; la tabla trimestral no se usa porque su total es 0."),
            ("interest_expense", interest, "Gastos de intereses del periodo."),
        ):
            self.add(
                section="debt",
                metric=metric,
                period=period,
                value=observation.numeric_value if observation else None,
                source=observation,
                notes=note,
            )
        total_debt = total.numeric_value if total else None
        equity_obs = self.balance_obs(period, "patrimonio neto")
        # Use detailed equity from the balance section, not the reported equity.
        capital = self.balance_value(period, "capital")
        reserves = self.balance_value(period, "reservas")
        result = self.balance_value(period, "resultado desp impuestos")
        detailed_equity = (
            capital + reserves + result
            if capital is not None and reserves is not None and result is not None
            else None
        )
        self.add(
            section="debt",
            metric="debt_to_equity",
            period=period,
            value=(total_debt / detailed_equity) if total_debt is not None and detailed_equity not in (None, 0) else None,
            unit="ratio",
            status="unreconciled",
            sources=[total, equity_obs],
            source_unreconciled=True,
            derived_from="total_debt / detailed_equity",
            reconciliation_status="not_applicable",
            tolerance_eur=0.0,
            notes="Derivado; el patrimonio detallado está marcado unreconciled.",
        )

    def build_cash(self, period: int) -> None:
        closing = self.balance_obs(period, "efectivo disponible")
        opening = self.balance_obs(period - 1, "efectivo disponible")
        closing_value = closing.numeric_value if closing else None
        opening_value = opening.numeric_value if opening else None
        net_change = (
            closing_value - opening_value
            if closing_value is not None and opening_value is not None
            else None
        )
        self.add(
            section="cash_flow",
            metric="opening_cash",
            period=period,
            value=opening_value,
            source=opening,
            notes=f"Caja de cierre {period - 1}.",
        )
        self.add(
            section="cash_flow",
            metric="net_cash_change",
            period=period,
            value=net_change,
            sources=[opening, closing],
            derived_from="closing_cash - opening_cash",
            status="confirmed",
            reconciliation_status="exact",
        )
        self.add(
            section="cash_flow",
            metric="closing_cash",
            period=period,
            value=closing_value,
            source=closing,
            reconciliation_status="exact",
        )

        net_result = next(
            row for row in self.rows
            if row.section == "income_statement" and row.metric == "net_result_after_taxes" and row.period == period
        )
        depreciation = next(
            row for row in self.rows
            if row.section == "income_statement" and row.metric == "depreciation_expenses" and row.period == period
        )
        factory_depreciation_obs = self.find(
            period,
            "Balance",
            "Gasto Deprec Fabrica",
            scope_contains="Análisis del Activo Fijo",
        )
        factory_depreciation = (
            factory_depreciation_obs.numeric_value if factory_depreciation_obs else None
        )
        ar_now_obs = self.balance_obs(period, "cuentas por cobrar neto")
        ar_prev_obs = self.balance_obs(period - 1, "cuentas por cobrar neto")
        inv_now_obs = self.balance_obs(period, "inventario")
        inv_prev_obs = self.balance_obs(period - 1, "inventario")
        ap_now_obs = self.balance_obs(period, "proveedores")
        ap_prev_obs = self.balance_obs(period - 1, "proveedores")
        tax_now_obs = self.balance_obs(period, "impuestos pendientes de pago")
        tax_prev_obs = self.balance_obs(period - 1, "impuestos pendientes de pago")
        ar_now = ar_now_obs.numeric_value if ar_now_obs else None
        ar_prev = ar_prev_obs.numeric_value if ar_prev_obs else None
        inv_now = inv_now_obs.numeric_value if inv_now_obs else None
        inv_prev = inv_prev_obs.numeric_value if inv_prev_obs else None
        ap_now = ap_now_obs.numeric_value if ap_now_obs else None
        ap_prev = ap_prev_obs.numeric_value if ap_prev_obs else None
        tax_now = tax_now_obs.numeric_value if tax_now_obs else None
        tax_prev = tax_prev_obs.numeric_value if tax_prev_obs else None
        ar_cash = -(ar_now - ar_prev) if ar_now is not None and ar_prev is not None else None
        inv_cash = inv_prev - inv_now if inv_now is not None and inv_prev is not None else None
        ap_cash = ap_now - ap_prev if ap_now is not None and ap_prev is not None else None
        tax_cash = tax_now - tax_prev if tax_now is not None and tax_prev is not None else None
        for metric, value, status, pd, note, sources in (
            ("net_result_cash", net_result.value, net_result.status, net_result.pd_dependencies, "Resultado del periodo.", []),
            ("depreciation_cash", depreciation.value, depreciation.status, "", "Depreciación de la cuenta de resultados (no incluye la depreciación de fábrica embebida en coste de ventas).", []),
            ("factory_depreciation_cash", factory_depreciation, "confirmed", "", "Gasto Deprec Fábrica: ajuste no-cash embebido en el coste de ventas; fuente Balance.", [factory_depreciation_obs]),
            ("receivables_cash_effect", ar_cash, "pending", "", "Cambio de cuentas por cobrar; construcción del puente.", [ar_now_obs, ar_prev_obs]),
            ("inventory_cash_effect", inv_cash, "pending", "", "Cambio de inventario; construcción del puente.", [inv_now_obs, inv_prev_obs]),
            ("suppliers_cash_effect", ap_cash, "pending", "", "Cambio de proveedores; construcción del puente.", [ap_now_obs, ap_prev_obs]),
            ("taxes_cash_effect", tax_cash, "pending", "", "Cambio de impuestos pendientes; construcción del puente.", [tax_now_obs, tax_prev_obs]),
        ):
            self.add(
                section="cash_flow",
                metric=metric,
                period=period,
                value=value,
                status=status,
                pd_dependencies=pd,
                notes=note,
                reconciliation_status="not_applicable",
                sources=sources,
                source_cells_override=(
                    net_result.source_cells
                    if metric == "net_result_cash"
                    else depreciation.source_cells
                    if metric == "depreciation_cash"
                    else _cells(sources)
                ),
            )

        operating = (
            (net_result.value or 0.0)
            + (depreciation.value or 0.0)
            + (factory_depreciation or 0.0)
            + (ar_cash or 0.0)
            + (inv_cash or 0.0)
            + (ap_cash or 0.0)
            + (tax_cash or 0.0)
        )
        self.add(
            section="cash_flow",
            metric="operating_cash_flow",
            period=period,
            value=operating,
            status=_status(net_result.status, "pending"),
            derived_from="net_result + depreciation_resultados + factory_depreciation + working_capital_changes",
            pd_dependencies=net_result.pd_dependencies,
            reconciliation_status="not_applicable",
            notes="Puente mínimo; incluye la depreciación de fábrica embebida en coste de ventas. No es un estado de flujo oficial.",
            source_cells_override=" | ".join(
                item
                for item in (
                    net_result.source_cells,
                    depreciation.source_cells,
                    _cells([factory_depreciation_obs]),
                    _cells([ar_now_obs, ar_prev_obs]),
                    _cells([inv_now_obs, inv_prev_obs]),
                    _cells([ap_now_obs, ap_prev_obs]),
                    _cells([tax_now_obs, tax_prev_obs]),
                )
                if item
            ),
        )

        gross_fixed_now_obs = self.balance_obs(period, "inmovilizado material bruto")
        gross_fixed_prev_obs = self.balance_obs(period - 1, "inmovilizado material bruto")
        intangible_now_obs = self.balance_obs(period, "inmovilizado intangible bruto")
        intangible_prev_obs = self.balance_obs(period - 1, "inmovilizado intangible bruto")
        financial_lp_now_obs = self.balance_obs(period, "activos financieros a lp")
        financial_lp_prev_obs = self.balance_obs(period - 1, "activos financieros a lp")
        financial_cp_now_obs = self.balance_obs(period, "activos financieros a cp")
        financial_cp_prev_obs = self.balance_obs(period - 1, "activos financieros a cp")
        investing = 0.0
        investing_sources: list[Observation | None] = []
        for now_obs, previous_obs in (
            (gross_fixed_now_obs, gross_fixed_prev_obs),
            (intangible_now_obs, intangible_prev_obs),
            (financial_lp_now_obs, financial_lp_prev_obs),
            (financial_cp_now_obs, financial_cp_prev_obs),
        ):
            now = now_obs.numeric_value if now_obs else None
            previous = previous_obs.numeric_value if previous_obs else None
            if now is not None and previous is not None:
                investing -= now - previous
                investing_sources.extend([now_obs, previous_obs])
        self.add(
            section="cash_flow",
            metric="investing_cash_flow",
            period=period,
            value=investing,
            sources=investing_sources,
            status="pending",
            derived_from="-(delta gross fixed assets + delta intangible + delta financial assets)",
            pd_dependencies="PD-07",
            reconciliation_status="not_applicable",
            notes="Inversión neta; la causa del CAPEX no está documentada (PD-07).",
        )

        debt_now_obs = self.debt_obs(period, "Total Deuda Bancaria")
        debt_prev_obs = self.debt_obs(period - 1, "Total Deuda Bancaria")
        debt_now = debt_now_obs.numeric_value if debt_now_obs else None
        debt_prev = debt_prev_obs.numeric_value if debt_prev_obs else None
        financing = debt_now - debt_prev if debt_now is not None and debt_prev is not None else None
        self.add(
            section="cash_flow",
            metric="financing_cash_flow",
            period=period,
            value=financing,
            sources=[debt_now_obs, debt_prev_obs],
            status="confirmed",
            derived_from="delta total_debt",
            reconciliation_status="not_applicable",
            notes="Cambio de deuda; dividendos y capital no incluidos en esta entrega.",
        )
        bridge_total = operating + investing + (financing or 0.0)
        residual = net_change - bridge_total if net_change is not None else None
        residual_status = (
            "exact"
            if _within(residual, self.config.exact_tolerance_eur)
            else "documented_residual"
            if _within(residual, self.config.documented_residual_eur)
            else "unreconciled"
        )
        self.add(
            section="cash_flow",
            metric="cash_bridge_total",
            period=period,
            value=bridge_total,
            status=_status(net_result.status, "pending"),
            derived_from="operating_cash_flow + investing_cash_flow + financing_cash_flow",
            pd_dependencies=net_result.pd_dependencies + ",PD-07",
            reconciliation_status="not_applicable",
            notes="Suma del puente mínimo, incluida la depreciación de fábrica no-cash.",
            source_cells_override=" | ".join(
                item for item in (
                    net_result.source_cells,
                    depreciation.source_cells,
                    _cells([factory_depreciation_obs]),
                    _cells(investing_sources),
                    _cells([debt_now_obs, debt_prev_obs]),
                ) if item
            ),
        )
        self.add(
            section="cash_flow",
            metric="cash_bridge_residual",
            period=period,
            value=residual,
            status="confirmed" if residual_status != "unreconciled" else "unreconciled",
            derived_from="net_cash_change - cash_bridge_total",
            reconciliation_status=residual_status,
            tolerance_eur=self.config.documented_residual_eur,
            notes=(
                "Residual del puente. El residual anterior coincidía con la Depreciación Fábrica "
                "(278.100 € en 2026 y 327.300 € en 2027) porque esa depreciación está embebida en el coste "
                "de ventas y no aparecía en la línea de Gastos de Depreciación de Resultados. "
                "Ahora se añade como ajuste no-cash explícito desde Balance."
            ),
            source_cells_override=" | ".join(
                item for item in (
                    net_result.source_cells,
                    depreciation.source_cells,
                    _cells([factory_depreciation_obs]),
                    _cells(investing_sources),
                    _cells([debt_now_obs, debt_prev_obs]),
                ) if item
            ),
        )

    def build_reconciliation(self, period: int) -> None:
        revenue_rows = [
            row for row in self.rows
            if row.section == "income_statement" and row.period == period and row.metric in {"revenue_total", "cost_of_sales_total", "gross_profit"}
        ]
        product_revenue = [
            row.value for row in self.rows
            if row.section == "income_statement" and row.period == period and row.metric.startswith("revenue_") and row.metric != "revenue_total"
        ]
        product_cost = [
            row.value for row in self.rows
            if row.section == "income_statement" and row.period == period and row.metric.startswith("cost_") and row.metric != "cost_of_sales_total"
        ]
        revenue_total = next((row for row in revenue_rows if row.metric == "revenue_total"), None)
        cost_total = next((row for row in revenue_rows if row.metric == "cost_of_sales_total"), None)
        gross = next((row for row in revenue_rows if row.metric == "gross_profit"), None)
        if revenue_total and revenue_total.value is not None and all(value is not None for value in product_revenue):
            difference = sum(product_revenue) - revenue_total.value
            self.add(
                section="reconciliation",
                metric="revenue_products_vs_total",
                period=period,
                value=difference,
                status=revenue_total.status,
                derived_from="sum(product revenue) - revenue_total",
                reconciliation_status="exact" if _within(difference, self.config.exact_tolerance_eur) else "unreconciled",
                tolerance_eur=self.config.exact_tolerance_eur,
            )
        if cost_total and cost_total.value is not None and all(value is not None for value in product_cost):
            difference = sum(product_cost) - cost_total.value
            self.add(
                section="reconciliation",
                metric="cost_products_vs_total",
                period=period,
                value=difference,
                status=cost_total.status,
                derived_from="sum(product cost) - cost_total",
                reconciliation_status=(
                    "exact"
                    if _within(difference, self.config.exact_tolerance_eur)
                    else "documented_residual"
                    if _within(difference, self.config.documented_residual_eur)
                    else "unreconciled"
                ),
                tolerance_eur=self.config.documented_residual_eur,
            )

        balance_rows = {
            row.metric: row for row in self.rows
            if row.section == "balance" and row.period == period
        }
        if "balance_detail_residual" in balance_rows:
            residual = balance_rows["balance_detail_residual"].value
            self.add(
                section="reconciliation",
                metric="balance_detail_identity",
                period=period,
                value=residual,
                status="unreconciled",
                source_unreconciled=True,
                derived_from="total_assets - (total_liabilities + detailed_equity)",
                reconciliation_status="documented_residual" if _within(residual, self.config.documented_residual_eur) else "unreconciled",
                tolerance_eur=self.config.documented_residual_eur,
                notes="Conciliación aritmética con residual de 1 €; la fuente sigue unreconciled.",
                source_cells_override=" | ".join(
                    item for item in (
                        balance_rows.get("total_assets").source_cells if balance_rows.get("total_assets") else "",
                        balance_rows.get("total_liabilities").source_cells if balance_rows.get("total_liabilities") else "",
                        balance_rows.get("detailed_equity").source_cells if balance_rows.get("detailed_equity") else "",
                    ) if item
                ),
            )
        if "balance_reported_residual" in balance_rows:
            residual = balance_rows["balance_reported_residual"].value
            self.add(
                section="reconciliation",
                metric="balance_reported_identity",
                period=period,
                value=residual,
                status="unreconciled",
                source_unreconciled=True,
                derived_from="total_assets - (total_liabilities + reported_equity)",
                reconciliation_status="unreconciled",
                tolerance_eur=self.config.documented_residual_eur,
                source_cells_override=" | ".join(
                    item for item in (
                        balance_rows.get("total_assets").source_cells if balance_rows.get("total_assets") else "",
                        balance_rows.get("total_liabilities").source_cells if balance_rows.get("total_liabilities") else "",
                        balance_rows.get("reported_equity").source_cells if balance_rows.get("reported_equity") else "",
                    ) if item
                ),
            )
        debt_total = next(
            (row for row in self.rows if row.section == "debt" and row.period == period and row.metric == "total_debt"),
            None,
        )
        if debt_total and debt_total.value is not None:
            debt_components = {
                row.metric: row.value for row in self.rows
                if row.section == "debt" and row.period == period
            }
            expected_debt = sum(
                debt_components.get(metric) or 0.0
                for metric in (
                    "long_term_debt",
                    "short_term_debt_direct",
                    "current_portion_long_term_debt",
                    "extraordinary_debt",
                )
            )
            difference = expected_debt - debt_total.value
            self.add(
                section="reconciliation",
                metric="debt_total_check",
                period=period,
                value=difference,
                status=debt_total.status,
                derived_from="LP + CP directo + porción corriente LP + extraordinario - total_debt",
                reconciliation_status="exact" if _within(difference, self.config.exact_tolerance_eur) else "unreconciled",
                tolerance_eur=self.config.exact_tolerance_eur,
            )
        cash_rows = {
            row.metric: row for row in self.rows
            if row.section == "cash_flow" and row.period == period
        }
        if "net_cash_change" in cash_rows and "closing_cash" in cash_rows and "opening_cash" in cash_rows:
            expected = (cash_rows["opening_cash"].value or 0.0) + (cash_rows["net_cash_change"].value or 0.0)
            difference = expected - (cash_rows["closing_cash"].value or 0.0)
            self.add(
                section="reconciliation",
                metric="cash_change_check",
                period=period,
                value=difference,
                status="confirmed",
                derived_from="opening_cash + net_cash_change - closing_cash",
                reconciliation_status="exact" if _within(difference, self.config.exact_tolerance_eur) else "unreconciled",
                tolerance_eur=self.config.exact_tolerance_eur,
            )
        if "cash_bridge_residual" in cash_rows:
            residual = cash_rows["cash_bridge_residual"].value
            residual_status = (
                "exact"
                if _within(residual, self.config.exact_tolerance_eur)
                else "documented_residual"
                if _within(residual, self.config.documented_residual_eur)
                else "unreconciled"
            )
            self.add(
                section="reconciliation",
                metric="cash_bridge_residual",
                period=period,
                value=residual,
                status="confirmed" if residual_status != "unreconciled" else "unreconciled",
                derived_from="net_cash_change - cash_bridge_total",
                reconciliation_status=residual_status,
                tolerance_eur=self.config.documented_residual_eur,
                notes="Residual del puente tras incluir la Depreciación Fábrica como ajuste no-cash.",
                source_cells_override=cash_rows["cash_bridge_residual"].source_cells,
            )

    def build(self) -> list[F2Row]:
        for period in (2026, 2027):
            self.build_income_statement(period)
            self.build_balance(period)
            self.build_debt(period)
            self.build_cash(period)
            self.build_reconciliation(period)
        self.rows.sort(key=lambda row: (row.section, row.period, row.metric))
        return self.rows


def _balance_anomaly_records(pipeline: PipelineResult) -> list[dict[str, Any]]:
    return [
        {
            "anomaly_id": anomaly.anomaly_id,
            "rule_id": anomaly.rule_id,
            "severity": anomaly.severity,
            "source_id": anomaly.source_id,
            "sheet": anomaly.sheet,
            "cell": anomaly.cell,
            "period": anomaly.period,
            "status": "unreconciled",
        }
        for anomaly in pipeline.anomalies
        if anomaly.category == "balance"
    ]


def run_f2(
    f1_config: F1Config | None = None,
    f2_config: F2Config | None = None,
) -> F2Result:
    resolved_f1 = f1_config or load_config()
    resolved_f2 = f2_config or load_f2_config(project_root=resolved_f1.project_root)
    pipeline = run_pipeline(resolved_f1)
    builder = Builder(pipeline, resolved_f2)
    rows = builder.build()
    anomalies = _balance_anomaly_records(pipeline)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    critical = sum(1 for anomaly in anomalies if anomaly["severity"] == "critical")
    manifest = {
        "schema_version": "f2.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(resolved_f2.output_dir),
        "config": {
            "exact_tolerance_eur": resolved_f2.exact_tolerance_eur,
            "documented_residual_eur": resolved_f2.documented_residual_eur,
        },
        "sources": [source.to_dict() for source in pipeline.sources],
        "summary": {
            "rows": len(rows),
            "status_counts": counts,
            "balance_anomalies": len(anomalies),
            "critical_balance_anomalies": critical,
            "unreconciled_balance_anomalies": len(anomalies),
        },
        "balance_anomalies": anomalies,
        "files": [
            "income_statement.csv",
            "balance.csv",
            "debt.csv",
            "cash_flow.csv",
            "reconciliation.csv",
            "manifest.json",
            "report.md",
        ],
    }
    return F2Result(
        f1_config=resolved_f1,
        f2_config=resolved_f2,
        pipeline=pipeline,
        rows=rows,
        balance_anomalies=anomalies,
        manifest=manifest,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cg_01.f2_engine", description="F2.1: motor financiero determinista.")
    parser.add_argument("--config", type=Path, default=None, help="Ruta a config/f1.toml.")
    parser.add_argument("--f2-config", type=Path, default=None, help="Ruta a config/f2.toml.")
    parser.add_argument("--output", type=Path, default=None, help="Directorio de salida F2.")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    from .f2_report import write_f2_outputs

    f1_config = load_config(args.config)
    f2_config = load_f2_config(
        args.f2_config,
        output_dir=args.output,
        project_root=f1_config.project_root,
    )
    result = run_f2(f1_config, f2_config)
    write_f2_outputs(result, f2_config.output_dir)
    if not args.quiet:
        counts = result.manifest["summary"]["status_counts"]
        print(
            f"F2.1 completado: {len(result.rows)} filas, "
            f"balance anomalies={result.manifest['summary']['balance_anomalies']} "
            f"(críticas={result.manifest['summary']['critical_balance_anomalies']})."
        )
        print(f"Estados: {json.dumps(counts, ensure_ascii=False, sort_keys=True)}")
        print(f"Salida: {f2_config.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
