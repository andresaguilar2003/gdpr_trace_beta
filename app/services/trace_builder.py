from app.models.trace import Trace
from app.models.original_event import OriginalEvent
from app.models.gdpr_event import GDPREvent
from app.models.context import Context
from app.specifications.activity_gdpr_mapping import ACTIVITY_GDPR_PATTERNS
from app.specifications.event_position import EventPosition
from app.models.user_right_type import UserRightType
from app.models.activity import Activity


IGNORED_KEYS = {
    "concept:name",
    "time:timestamp",
    "lifecycle:transition"
}

def _get_attr(log, trace, key):
    val = trace.attributes.get(key)

    if val is None:
        val = log.attributes.get(key)

    if hasattr(val, "value"):
        return val.value

    if isinstance(val, dict):
        return val.get("value")

    return val


def _unwrap_attr(value):
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return value.get("value")
    return value


def _attributes_to_dict(attributes):
    return {key: _unwrap_attr(value) for key, value in dict(attributes or {}).items()}


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    normalized = str(_unwrap_attr(value)).strip().lower()
    return normalized in {"true", "1", "yes", "y"}


def _parse_position(value):
    if value is None:
        return None
    if isinstance(value, EventPosition):
        return value

    normalized = str(_unwrap_attr(value)).strip().split(".")[-1].upper()
    return EventPosition.__members__.get(normalized)


def _parse_activity_type(value):
    if value is None:
        return None

    from app.specifications.activity_types import ActivityType

    if isinstance(value, ActivityType):
        return value

    normalized = str(_unwrap_attr(value)).strip().split(".")[-1].upper()
    return ActivityType.__members__.get(normalized)


def _parse_user_right_type(value):
    if value is None:
        return None
    if isinstance(value, UserRightType):
        return value

    normalized = str(_unwrap_attr(value)).strip().split(".")[-1].upper()
    return UserRightType.__members__.get(normalized)


def _first_real_value(*values):
    for value in values:
        value = _unwrap_attr(value)
        if value is None:
            continue
        if str(value).strip().lower() in {"", "none", "null"}:
            continue
        return value
    return None


def _build_context(log_attrs, trace_attrs):
    attrs = {}
    attrs.update(_attributes_to_dict(log_attrs))
    attrs.update(_attributes_to_dict(trace_attrs))

    return Context(
        purpose=_first_real_value(attrs.get("gdpr:purpose"), attrs.get("purpose")),
        legal_basis=_first_real_value(attrs.get("gdpr:legal_basis"), attrs.get("gdpr:legalBasis"), attrs.get("legal_basis")),
        data_category=_first_real_value(attrs.get("gdpr:data_category"), attrs.get("gdpr:dataCategory"), attrs.get("data_category")),
        data_subject_type=_first_real_value(attrs.get("gdpr:data_subject_type"), attrs.get("gdpr:dataSubjectType"), attrs.get("data_subject_type")),
        processing_operation=_first_real_value(attrs.get("gdpr:processing_operation"), attrs.get("gdpr:processingOperation"), attrs.get("processing_operation")),
        retention_period=_first_real_value(attrs.get("gdpr:retention_period"), attrs.get("gdpr:retentionPeriod"), attrs.get("retention_period")),
        processing_domain=_first_real_value(attrs.get("gdpr:processing_domain"), attrs.get("gdpr:processingDomain"), attrs.get("processing_domain")),
        has_third_party_recipients=_parse_bool(
            _first_real_value(
                attrs.get("gdpr:has_third_party_recipients"),
                attrs.get("gdpr:third_party_recipients"),
                attrs.get("gdpr:hasThirdPartyRecipients"),
                attrs.get("has_third_party_recipients"),
            )
        ),
        international_transfer=_first_real_value(
            attrs.get("gdpr:international_transfer"),
            attrs.get("gdpr:internationalTransfer"),
            attrs.get("international_transfer"),
        ) or "none",
        transfer_safeguard=_first_real_value(
            attrs.get("gdpr:transfer_safeguard"),
            attrs.get("gdpr:transferSafeguard"),
            attrs.get("transfer_safeguard"),
        ) or "none",
        consent_status=_first_real_value(
            attrs.get("gdpr:consent_status"),
            attrs.get("gdpr:consentStatus"),
            attrs.get("consent_status"),
        ) or "not_needed",
    )


def _expected_position_for_gdpr_event(name):
    for rules in ACTIVITY_GDPR_PATTERNS.values():
        for rule in rules:
            if rule["event"] == name:
                return rule["position"]
    return None

def build_traces_from_pm4py_log(log):

    traces = []
    log_attributes = _attributes_to_dict(getattr(log, "attributes", {}))

    for case_index, pm_trace in enumerate(log):

        trace = Trace(
            trace_id=f"case_{index_value(pm_trace, case_index)}",
            context=_build_context(log_attributes, getattr(pm_trace, "attributes", {})),
        )
        trace.attributes = _attributes_to_dict(getattr(pm_trace, "attributes", {}))
        trace.log_attributes = dict(log_attributes)

        trace_attributes = set(pm_trace.attributes.keys())

        for order, event in enumerate(pm_trace):

            name = event.get("concept:name")
            timestamp = event.get("time:timestamp")
            from app.specifications.activity_types import ActivityType

            activity_type = _parse_activity_type(event.get("gdpr:activity_type"))
            user_right_type = _parse_user_right_type(event.get("gdpr:user_right_type"))
            # -------------------------
            # atributos reales
            # -------------------------
            attributes = {}

            for k, v in event.items():

                if k in IGNORED_KEYS:
                    continue

                if k in trace_attributes:
                    continue

                attributes[k] = v

            # =====================================================
            # GDPR EVENT
            # =====================================================

            if activity_type == ActivityType.GDPR_COMPLIANCE:

                position = _parse_position(event.get("gdpr:position"))
                if position is None:
                    position = _expected_position_for_gdpr_event(name)

                ev = GDPREvent(
                    event_id=f"{case_index}_{order}",
                    name=name,
                    timestamp=timestamp,
                    order=order,
                    position=position,
                )

            # =====================================================
            # ORIGINAL EVENT
            # =====================================================

            else:

                ev = OriginalEvent(
                    event_id=f"{case_index}_{order}",
                    name=name,
                    timestamp=timestamp,
                    order=order,
                    raw_label=name,
                    attributes=attributes
                )

                # 🔥 CRÍTICO para validadores
                ev.activity = Activity(
                    activity_id=f"{case_index}_{order}",
                    label=name,
                    activity_type=activity_type
                )

                ev.activity.user_right_type = user_right_type

                ev.user_right_type = user_right_type

            # 👉 añadir SIEMPRE
            trace.add_event(ev)

        # 👉 añadir trace fuera del loop de eventos
        traces.append(trace)

    return traces


def index_value(pm_trace, fallback):
    name = getattr(pm_trace, "attributes", {}).get("concept:name")
    name = _unwrap_attr(name)
    return name if name is not None else fallback
