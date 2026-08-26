from app.models.gdpr_event import GDPREvent
from app.models.user_right_type import UserRightType
from app.specifications.activity_gdpr_mapping import ACTIVITY_GDPR_PATTERNS
from app.specifications.activity_types import ActivityType
from app.specifications.data_categories import DataCategory
from app.specifications.event_position import EventPosition


class GDPREnrichmentValidator:

    @staticmethod
    def validate(trace):

        violations = []
        warnings = []

        v, w = GDPREnrichmentValidator._case_start_rules(trace)
        violations.extend(v)
        warnings.extend(w)

        v, w = GDPREnrichmentValidator._data_collection_rules(trace)
        violations.extend(v)
        warnings.extend(w)

        v, w = GDPREnrichmentValidator._data_processing_rules(trace)
        violations.extend(v)
        warnings.extend(w)

        v, w = GDPREnrichmentValidator._data_access_rules(trace)
        violations.extend(v)
        warnings.extend(w)

        v, w = GDPREnrichmentValidator._data_transfer_rules(trace)
        violations.extend(v)
        warnings.extend(w)

        v, w = GDPREnrichmentValidator._automated_decision_rules(trace)
        violations.extend(v)
        warnings.extend(w)

        v, w = GDPREnrichmentValidator._data_deletion_rules(trace)
        violations.extend(v)
        warnings.extend(w)

        v, w = GDPREnrichmentValidator._user_right_request_rules(trace)
        violations.extend(v)
        warnings.extend(w)

        v, w = GDPREnrichmentValidator._case_end_rules(trace)
        violations.extend(v)
        warnings.extend(w)

        return {
            "violations": violations,
            "warnings": warnings
        }

    @staticmethod
    def _name(event):
        return getattr(event, "name", None)

    @staticmethod
    def _order(event):
        return getattr(event, "order", 0)

    @staticmethod
    def _position(event):
        position = getattr(event, "position", None)
        if isinstance(position, EventPosition):
            return position
        if position is None:
            return None

        value = getattr(position, "value", position)
        normalized = str(value).split(".")[-1].upper()

        if normalized == "BEFORE":
            return EventPosition.BEFORE
        if normalized == "AFTER":
            return EventPosition.AFTER
        return None

    @staticmethod
    def _activity_type(event):
        if isinstance(event, GDPREvent):
            return ActivityType.GDPR_COMPLIANCE

        activity = getattr(event, "activity", None)
        activity_type = getattr(activity, "type", None) or getattr(activity, "activity_type", None)
        if isinstance(activity_type, ActivityType):
            return activity_type
        if activity_type is None:
            activity_type = getattr(event, "activity_type", None)
        if isinstance(activity_type, ActivityType):
            return activity_type
        if activity_type is None:
            return None

        normalized = str(activity_type).split(".")[-1].upper()
        return ActivityType.__members__.get(normalized)

    @staticmethod
    def _is_gdpr_event(event):
        if isinstance(event, GDPREvent):
            return True
        return GDPREnrichmentValidator._activity_type(event) == ActivityType.GDPR_COMPLIANCE

    @staticmethod
    def _context_value(trace, attr_name):
        ctx = getattr(trace, "context", None)
        value = getattr(ctx, attr_name, None) if ctx is not None else None
        if value is not None:
            return value

        aliases = {
            "purpose": ["gdpr:purpose", "gdpr:processing_purpose", "gdpr:processingPurpose"],
            "legal_basis": ["gdpr:legal_basis", "gdpr:legalBasis"],
            "data_category": ["gdpr:data_category", "gdpr:dataCategory"],
            "data_subject_type": ["gdpr:data_subject_type", "gdpr:dataSubjectType"],
            "processing_operation": ["gdpr:processing_operation", "gdpr:processingOperation"],
            "processing_domain": ["gdpr:processing_domain", "gdpr:processingDomain"],
            "has_third_party_recipients": [
                "gdpr:has_third_party_recipients",
                "gdpr:third_party_recipients",
                "gdpr:hasThirdPartyRecipients",
            ],
            "international_transfer": ["gdpr:international_transfer", "gdpr:internationalTransfer"],
            "retention_period": ["gdpr:retention_period", "gdpr:retentionPeriod"],
            "transfer_safeguard": ["gdpr:transfer_safeguard", "gdpr:transferSafeguard"],
            "consent_status": ["gdpr:consent_status", "gdpr:consentStatus"],
        }

        for attributes in (
            getattr(trace, "attributes", None),
            getattr(trace, "log_attributes", None),
        ):
            if not isinstance(attributes, dict):
                continue
            for key in aliases.get(attr_name, [f"gdpr:{attr_name}"]):
                if key in attributes:
                    return attributes[key]

        return None

    @staticmethod
    def _expected_position(gdpr_event_name):
        for rules in ACTIVITY_GDPR_PATTERNS.values():
            for rule in rules:
                if rule.get("event") == gdpr_event_name:
                    return rule.get("position")
        return None

    @staticmethod
    def _normalized_value(value):
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        raw_value = getattr(value, "value", value)
        normalized = str(raw_value).strip()
        if "." in normalized:
            normalized = normalized.split(".")[-1]
        return normalized.lower()

    @staticmethod
    def _is_sensitive_category(value):
        normalized = GDPREnrichmentValidator._normalized_value(value)
        return normalized in {"health", "special", "biometric", "genetic", "children", "vulnerable"}

    @staticmethod
    def _is_standard_category(value):
        return GDPREnrichmentValidator._normalized_value(value) == "standard"

    @staticmethod
    def _is_truthy(value):
        if isinstance(value, bool):
            return value
        return GDPREnrichmentValidator._normalized_value(value) in {"true", "1", "yes", "y"}

    @staticmethod
    def _is_consent_legal_basis(value):
        return GDPREnrichmentValidator._normalized_value(value) == "consent"

    # =====================================================
    # CASE_START RULES
    # =====================================================

    @staticmethod
    def _case_start_rules(trace):

        violations = []
        warnings = []



        # --------------------------------------------------
        # localizar CASE_START
        # --------------------------------------------------

        case_start_events = [
            e
            for e in trace.events
            if e.name == "CASE_START"
        ]


        for event in case_start_events:

            verify_events = [
                e
                for e in trace.events
                if (
                    e.name == "verify_legal_basis"
                )
            ]
            
            if len(verify_events) > 1:

                violations.append({
                    "rule": "CASE_START_VERIFY_LEGAL_BASIS_DUPLICATED",
                    "event": "CASE_START",
                    "message": (
                        f"verify_legal_basis appears "
                        f"{len(verify_events)} times"
                    ),
                    "recommendation": "Ensure the system logs 'verify_legal_basis' exactly once per process instance to prevent redundancy and overhead in the audit trail."
                })


            has_event = any(
                e.name == "verify_legal_basis"
                and GDPREnrichmentValidator._position(e) == EventPosition.AFTER
                and e.order > event.order
                for e in trace.events
            )


            if not has_event:

                violations.append({
                    "rule": "CASE_START_VERIFY_LEGAL_BASIS",
                    "event": "CASE_START",
                    "message": (
                        "Missing verify_legal_basis "
                        "AFTER CASE_START"
                    ),
                    "recommendation": "Inject a 'verify_legal_basis' event immediately after 'CASE_START'. Under GDPR Art. 6, processing is only lawful if a valid legal basis is verified prior to executing any workflow operational activities."
                })


        return violations, warnings




    @staticmethod
    def _case_end_rules(trace):
        """
        OCL:
        context Trace
        
        inv CASE_END_MISSING_RETENTION_CONTEXT:
            events->exists(e | e.type = CASE_END) implies not context.retention_period.oclIsUndefined()

        inv CASE_END_RETENTION_VERIFY:
            for all e in events where e.type = CASE_END:
                exists g in events such that
                    g.name = 'retention_period_verify' AND
                    g.position = BEFORE AND
                    g.order < e.order

        inv CASE_END_ERASURE:
            for all e in events where e.type = CASE_END:
                if not context.retention_period.oclIsUndefined() then
                    exists g in events such that
                        g.name = 'confirm_data_erasure' AND
                        g.position = BEFORE AND
                        g.order < e.order
                else
                    true
                endif
        """
        violations = []
        warnings = []

        # --------------------------------------------------
        # localizar CASE_END
        # --------------------------------------------------
        # Adaptado para identificar eventos de tipo CASE_END según tu estructura original
        case_end_events = [
            e
            for e in trace.events
            if (
                not GDPREnrichmentValidator._is_gdpr_event(e)
                and GDPREnrichmentValidator._activity_type(e) == ActivityType.CASE_END
            )
        ]

        for event in case_end_events:

            # 1. Regla: CASE_END_MISSING_RETENTION_CONTEXT
            if GDPREnrichmentValidator._context_value(trace, "retention_period") is None:
                violations.append({
                    "rule": "CASE_END_MISSING_RETENTION_CONTEXT",
                    "event": "CASE_END",
                    "message": "Missing retention_period in context",
                    "recommendation": "Configure a retention policy in your global data metadata context. GDPR requires that personal data is kept in a form which permits identification of data subjects for no longer than is necessary."
                })

            # -------------------------
            # retention_period_verify (SIEMPRE)
            # -------------------------
            retention_events = [
                e
                for e in trace.events
                if (
                    GDPREnrichmentValidator._is_gdpr_event(e)
                    and e.name == "retention_period_verify"
                    and GDPREnrichmentValidator._position(e) == EventPosition.BEFORE
                )
            ]

            has_retention = any(
                r.order < event.order 
                for r in retention_events
            )


            if not has_retention:
                violations.append({
                    "rule": "CASE_END_RETENTION_VERIFY",
                    "event": event.name,
                    "message": "Missing retention_period_verify BEFORE CASE_END",
                    "recommendation": f"Inject a 'retention_period_verify' compliance check BEFORE '{event.name}'. At the end of a process instance, the data lifecycle controller must evaluate if the data must be archived, anonymized, or scheduled for deletion."
                })

            # -------------------------
            # confirm_data_erasure (CONDICIONAL)
            # -------------------------
            if GDPREnrichmentValidator._context_value(trace, "retention_period") is not None:
                erasure_events = [
                    e
                    for e in trace.events
                    if (
                        GDPREnrichmentValidator._is_gdpr_event(e)
                        and e.name == "confirm_data_erasure"
                        and GDPREnrichmentValidator._position(e) == EventPosition.BEFORE
                    )
                ]


                has_erasure = any(
                    er.order < event.order 
                    for er in erasure_events
                )

                if not has_erasure:
                    violations.append({
                        "rule": "CASE_END_ERASURE",
                        "event": event.name,
                        "message": "Missing confirm_data_erasure BEFORE CASE_END",
                        "recommendation": f"Inject a 'confirm_data_erasure' event prior to '{event.name}'. To fulfill the GDPR data minimization and limited retention principles, once a business case reaches its final state, technical mechanisms must confirm data cleanup actions."
                    })

        return violations, warnings
    
    
    # =====================================================
    # DATA_COLLECTION RULES
    # =====================================================

    @staticmethod
    def _data_collection_rules(trace):
        """
        DATA_COLLECTION RULES (Corregido para detectar mutaciones globales de Consentimiento y Privacy Notice)
        """
        violations = []
        warnings = []

        legal_basis_value = GDPREnrichmentValidator._context_value(trace, "legal_basis")
        legal_basis = GDPREnrichmentValidator._normalized_value(legal_basis_value)
        requires_consent = GDPREnrichmentValidator._is_consent_legal_basis(legal_basis_value)
        collection_events = [
            event
            for event in trace.events
            if (
                not GDPREnrichmentValidator._is_gdpr_event(event)
                and GDPREnrichmentValidator._activity_type(event) == ActivityType.DATA_COLLECTION
            )
        ]

        if not collection_events:
            return violations, warnings

        # 1. Comprobaciones globales de existencia en la traza
        has_consent = any(
            GDPREnrichmentValidator._is_gdpr_event(e)
            and getattr(e, "name", None) == "check_consent"
            for e in trace.events
        )

        has_notice = any(
            hasattr(e, 'name') and e.name == "privacy_notice_disclosed"
            for e in trace.events
        )

        # -----------------------------------------------------------
        # REGLAS GLOBALES DE EXISTENCIA (Garantiza que salten aunque se borren del dataset)
        # -----------------------------------------------------------
        
        # REGLA PRIVACY NOTICE: Obligatorio según OCL siempre que haya recolección de datos en el proceso context
        if not has_notice:
            violations.append({
                "rule": "DATA_COLLECTION_NOTICE",
                "event": "trace",
                "message": "Missing privacy_notice_disclosed in trace",
                "recommendation": "Inject a 'privacy_notice_disclosed' event into the trace. GDPR Art. 13 mandates that data subjects must be provided with clear and transparent privacy information."
            })

        if not requires_consent and has_consent:
            warnings.append({
                "rule": "DATA_COLLECTION_CONSENT_FORBIDDEN",
                "event": "trace",
                "message": f"check_consent should NOT exist when legal_basis is '{legal_basis or 'undefined'}'",
                "recommendation": f"Remove the 'check_consent' activity. Since the current legal basis is established as '{legal_basis or 'undefined'}', invoking consent verification causes unnecessary data processing under GDPR Art. 5/25."
            })


        # -----------------------------------------------------------
        # BUCLE PARA EVALUAR REGLAS DE POSICIÓN / FLUJO CRONOLÓGICO
        # -----------------------------------------------------------
        for event in collection_events:

            # -------------------------
            # RULE 1: privacy_notice_disclosed (Validación de orden posicional si existe)
            # -------------------------
            if has_notice:
                valid_notice_position = any(
                    hasattr(e, 'name') and e.name == "privacy_notice_disclosed"
                    and GDPREnrichmentValidator._position(e) == GDPREnrichmentValidator._expected_position("privacy_notice_disclosed")
                    and getattr(e, 'order', 0) >= getattr(event, 'order', 0)
                    for e in trace.events
                )

                if not valid_notice_position:
                    violations.append({
                        "rule": "DATA_COLLECTION_NOTICE",
                        "event": event.name,
                        "message": "privacy_notice_disclosed exists but it is not positioned AFTER data collection",
                        "recommendation": f"Move 'privacy_notice_disclosed' so its position is AFTER the collection activity '{event.name}'."
                    })

            # -------------------------
            # RULE 2 & 3: check_consent (required only for legal_basis == consent)
            # -------------------------
            if requires_consent:
                valid_consent_position = any(
                    GDPREnrichmentValidator._is_gdpr_event(e)
                    and getattr(e, "name", None) == "check_consent"
                    and GDPREnrichmentValidator._position(e) == GDPREnrichmentValidator._expected_position("check_consent")
                    and getattr(e, 'order', 0) < getattr(event, 'order', 0)
                    for e in trace.events
                )

                if not valid_consent_position:
                    violations.append({
                        "rule": "DATA_COLLECTION_CONSENT_REQUIRED",
                        "event": event.name,
                        "message": "Missing check_consent BEFORE data collection while legal_basis is consent",
                        "recommendation": f"Inject or move 'check_consent' so it is a GDPR event with position BEFORE and order lower than the collection activity '{event.name}'."
                    })

            # -------------------------
            # RULE 4: legal basis must be initialized at trace start
            # -------------------------
            has_case_start_before = any(
                hasattr(e, 'name') and e.name == "CASE_START"
                and getattr(e, 'order', 0) < getattr(event, 'order', 0)
                for e in trace.events
            )

            has_legal_basis_after_start = any(
                hasattr(e, 'name') and e.name == "verify_legal_basis"
                and getattr(e, 'order', 0) < getattr(event, 'order', 0)
                for e in trace.events
            )

            if not (has_case_start_before and has_legal_basis_after_start):
                violations.append({
                    "rule": "DATA_COLLECTION_LEGAL_BASIS_FLOW",
                    "event": event.name,
                    "message": "Missing CASE_START + verify_legal_basis before DATA_COLLECTION",
                    "recommendation": f"Re-order the event trace so that 'CASE_START' and 'verify_legal_basis' execute chronologically before '{event.name}'."
                })

            # -------------------------
            # RULE 5: record_purpose (REQUIRED ANYWHERE)
            # -------------------------
            has_purpose = any(
                hasattr(e, 'name') and e.name == "record_purpose"
                for e in trace.events
            )

            if not has_purpose:
                violations.append({
                    "rule": "DATA_COLLECTION_PURPOSE_REQUIRED",
                    "event": event.name,
                    "message": "Missing record_purpose",
                    "recommendation": f"Inject a 'record_purpose' log entry into the trace."
                })

        return violations, warnings



    # =====================================================
    # DATA_PROCESSING RULES
    # =====================================================

    @staticmethod
    def _data_processing_rules(trace):

        """
        OCL:
        context Trace

        inv DATA_PROCESSING_MINIMISATION:
            for all e where e.type = DATA_PROCESSING:
                exists g where
                    g.name = minimisation_check AND
                    g.position = BEFORE AND
                    g.order < e.order

        inv DATA_PROCESSING_ENCRYPTION_REQUIRED:
            if data_category != STANDARD:
                exists g where
                    g.name = encryption_applied AND
                    g.position = BEFORE AND
                    g.order < e.order

        inv DATA_PROCESSING_ENCRYPTION_FORBIDDEN:
            if data_category = STANDARD:
                not exists g where g.name = encryption_applied

        inv DATA_PROCESSING_LOG_REQUIRED:
            for all e where e.type = DATA_PROCESSING:
                exists g where
                    g.name = log_processing_activity
                OR
                exists g where
                    g.name = log_processing_activity AND
                    g.order > e.order
        """

        violations = []
        warnings = []

        data_category = GDPREnrichmentValidator._context_value(trace, "data_category")

        for event in trace.events:

            if GDPREnrichmentValidator._is_gdpr_event(event):
                continue
            if GDPREnrichmentValidator._activity_type(event) != ActivityType.DATA_PROCESSING:
                continue

            # -------------------------
            # RULE 1: minimisation_check (REQUIRED)
            # -------------------------

            has_min = any(
                GDPREnrichmentValidator._is_gdpr_event(e)
                and e.name == "minimisation_check"
                and GDPREnrichmentValidator._position(e) == EventPosition.BEFORE
                and e.order < event.order
                for e in trace.events
            )

            if not has_min:
                violations.append({
                    "rule": "DATA_PROCESSING_MINIMISATION",
                    "event": event.name,
                    "message": "Missing minimisation_check BEFORE",
                    "recommendation": f"Inject a 'minimisation_check' event with position BEFORE the processing activity '{event.name}'. Under GDPR Art. 5(1)(c), personal data must be adequate, relevant, and limited to what is strictly necessary in relation to the purposes for which they are processed."
                })

            # -------------------------
            # RULE 2: encryption_applied
            # -------------------------

            has_encryption = any(
                GDPREnrichmentValidator._is_gdpr_event(e)
                and e.name == "encryption_applied"
                for e in trace.events
            )

            # REQUIRED
            if data_category and not GDPREnrichmentValidator._is_standard_category(data_category):

                valid_position = any(
                    GDPREnrichmentValidator._is_gdpr_event(e)
                    and e.name == "encryption_applied"
                    and GDPREnrichmentValidator._position(e) == GDPREnrichmentValidator._expected_position("encryption_applied")
                    and e.order < event.order
                    for e in trace.events
                )

                if not valid_position:
                    violations.append({
                        "rule": "DATA_PROCESSING_ENCRYPTION_REQUIRED",
                        "event": event.name,
                        "message": "Missing encryption_applied BEFORE (non-standard data)",
                        "recommendation": f"Inject an 'encryption_applied' event with position BEFORE processing special or non-standard data in '{event.name}'. GDPR Art. 32 strictly requires implementing appropriate technical measures, such as pseudonymisation and encryption, to ensure a level of security appropriate to the risk."
                    })

            # FORBIDDEN
            else:

                if has_encryption:
                    warnings.append({
                        "rule": "DATA_PROCESSING_ENCRYPTION_FORBIDDEN",
                        "event": event.name,
                        "message": "encryption_applied should NOT exist for STANDARD data",
                        "recommendation": f"Remove or bypass the 'encryption_applied' check before '{event.name}'. The active context indicates only STANDARD data is processed; enforcing complex encryption workflows here introduces unnecessary computing overhead and breaks process efficiency models."
                    })

            # -------------------------
            # RULE 3: log_processing_activity (REQUIRED RELATED OR AFTER)
            # -------------------------

            has_log_related = any(
                GDPREnrichmentValidator._is_gdpr_event(e)
                and e.name == "log_processing_activity"
                for e in trace.events
            )

            has_log_after = any(
                GDPREnrichmentValidator._is_gdpr_event(e)
                and e.name == "log_processing_activity"
                and e.order > event.order
                for e in trace.events
            )

            if not (has_log_related or has_log_after):
                violations.append({
                    "rule": "DATA_PROCESSING_LOG_REQUIRED",
                    "event": event.name,
                    "message": "Missing log_processing_activity (related or after)",
                    "recommendation": f"Ensure a 'log_processing_activity' event is registered during or immediately AFTER the execution of '{event.name}'. To demonstrate accountability under GDPR, all operational processing state transitions must be immutably recorded in the process audit log."
                })

        return violations, warnings
    

    # =====================================================
    # DATA_ACCESS RULES
    # =====================================================

    @staticmethod
    def _data_access_rules(trace):

        """
        OCL:
        context Trace

        inv DATA_ACCESS_CONTROL_REQUIRED:
            if data_category in {HEALTH, SPECIAL}:
                exists g where
                    g.name = access_control_check AND
                    g.position = BEFORE AND
                    g.order < e.order

        inv DATA_ACCESS_CONTROL_FORBIDDEN:
            if data_category not in {HEALTH, SPECIAL}:
                not exists g where g.name = access_control_check
        """

        violations = []
        warnings = []

        data_category = GDPREnrichmentValidator._context_value(trace, "data_category")

        access_control_events = [
            e for e in trace.events
            if GDPREnrichmentValidator._is_gdpr_event(e) and e.name == "access_control_check"
        ]
        
        if len(access_control_events) > 1:
            violations.append({
                "rule": "DATA_ACCESS_CONTROL_DUPLICATED",
                "event": "trace",
                "message": f"access_control_check appears {len(access_control_events)} times",
                "recommendation": "Ensure the system logs 'access_control_check' exactly once. Multiple security check events suggest trace duplication or logging errors."
            })

        for event in trace.events:

            if GDPREnrichmentValidator._is_gdpr_event(event):
                continue

            if GDPREnrichmentValidator._activity_type(event) != ActivityType.DATA_ACCESS:
                continue

            # -------------------------
            # ¿EXISTE access_control_check?
            # -------------------------

            has_access_control = any(
                GDPREnrichmentValidator._is_gdpr_event(e)
                and e.name == "access_control_check"
                for e in trace.events
            )

            # -------------------------
            # CASO 1: REQUIRED
            # -------------------------

            if GDPREnrichmentValidator._is_sensitive_category(data_category):

                valid_position = any(
                    GDPREnrichmentValidator._is_gdpr_event(e)
                    and e.name == "access_control_check"
                    and GDPREnrichmentValidator._position(e) == GDPREnrichmentValidator._expected_position("access_control_check")
                    and e.order < event.order
                    for e in trace.events
                )

                if not valid_position:
                    violations.append({
                        "rule": "DATA_ACCESS_CONTROL_REQUIRED",
                        "event": event.name,
                        "message": "Missing access_control_check BEFORE (sensitive data)",
                        "recommendation": f"Inject an 'access_control_check' event with position BEFORE executing '{event.name}'. The trace context involves sensitive categories ({data_category}). Unauthorized internal access violations must be mitigated by verifying fine-grained privileges prior to data exposure."
                    })

            # -------------------------
            # CASO 2: FORBIDDEN
            # -------------------------

            else:

                if has_access_control:
                    warnings.append({
                        "rule": "DATA_ACCESS_CONTROL_FORBIDDEN",
                        "event": event.name,
                        "message": "access_control_check should NOT exist for non-sensitive data",
                        "recommendation": f"Remove the 'access_control_check' block prior to '{event.name}'. For standard data categories, generic system authentication is legally sufficient. Avoid operational friction or deadlocks in the process mining topology."
                    })

        return violations, warnings
    

    # =====================================================
    # DATA_TRANSFER RULES
    # =====================================================

    @staticmethod
    def _data_transfer_rules(trace):

        """
        OCL:
        context Trace

        inv DATA_TRANSFER_THIRD_PARTY_REQUIRED:
            if has_third_party_recipients = true:
                exists g where
                    g.name = check_third_party_agreement AND
                    g.position = BEFORE AND
                    g.order < e.order

        inv DATA_TRANSFER_THIRD_PARTY_FORBIDDEN:
            if has_third_party_recipients = false:
                not exists g where g.name = check_third_party_agreement

        inv DATA_TRANSFER_INTERNATIONAL_REQUIRED:
            if international_transfer = "third_country":
                exists g where
                    g.name = verify_international_safeguard AND
                    g.position = BEFORE AND
                    g.order < e.order

        inv DATA_TRANSFER_INTERNATIONAL_FORBIDDEN:
            if international_transfer != "third_country":
                not exists g where g.name = verify_international_safeguard
        """

        violations = []
        warnings = []

        has_third_party_recipients = GDPREnrichmentValidator._is_truthy(
            GDPREnrichmentValidator._context_value(trace, "has_third_party_recipients")
        )
        international_transfer = GDPREnrichmentValidator._normalized_value(
            GDPREnrichmentValidator._context_value(trace, "international_transfer")
        )

        has_third_party_check_global = any(
            GDPREnrichmentValidator._is_gdpr_event(e)
            and e.name == "check_third_party_agreement"
            for e in trace.events
        )

        has_international_check_global = any(
            GDPREnrichmentValidator._is_gdpr_event(e)
            and e.name == "verify_international_safeguard"
            for e in trace.events
        )
        transfer_events = [
            event
            for event in trace.events
            if (
                not GDPREnrichmentValidator._is_gdpr_event(event)
                and GDPREnrichmentValidator._activity_type(event) == ActivityType.DATA_TRANSFER
            )
        ]

        if not transfer_events and not has_third_party_recipients and has_third_party_check_global:
            warnings.append({
                "rule": "DATA_TRANSFER_THIRD_PARTY_FORBIDDEN",
                "event": "trace",
                "message": "check_third_party_agreement exists while has_third_party_recipients is false",
                "recommendation": "Remove 'check_third_party_agreement' from the trace or restore the third-party recipient context when an external recipient is actually involved."
            })

        if not transfer_events and international_transfer != "third_country" and has_international_check_global:
            warnings.append({
                "rule": "DATA_TRANSFER_INTERNATIONAL_FORBIDDEN",
                "event": "trace",
                "message": "verify_international_safeguard exists while international_transfer is not third_country",
                "recommendation": "Remove 'verify_international_safeguard' unless the context declares a third-country international transfer."
            })

        for event in transfer_events:

            # -------------------------
            # EXISTENCIA
            # -------------------------

            has_third_party_check = any(
                GDPREnrichmentValidator._is_gdpr_event(e)
                and e.name == "check_third_party_agreement"
                for e in trace.events
            )

            has_international_check = any(
                GDPREnrichmentValidator._is_gdpr_event(e)
                and e.name == "verify_international_safeguard"
                for e in trace.events
            )

            # =====================================================
            # 1. THIRD PARTY AGREEMENT
            # =====================================================

            if has_third_party_recipients:

                valid_position = any(
                    GDPREnrichmentValidator._is_gdpr_event(e)
                    and e.name == "check_third_party_agreement"
                    and GDPREnrichmentValidator._position(e) == GDPREnrichmentValidator._expected_position("check_third_party_agreement")
                    and e.order < event.order
                    for e in trace.events
                )

                if not valid_position:
                    violations.append({
                        "rule": "DATA_TRANSFER_THIRD_PARTY_REQUIRED",
                        "event": event.name,
                        "message": "Missing check_third_party_agreement BEFORE",
                        "recommendation": f"Inject a 'check_third_party_agreement' control event BEFORE '{event.name}'. Sharing data with external recipients mandates confirming that a valid Data Processing Agreement (DPA) or formal contract is actively enforced."
                    })

            else:

                if has_third_party_check:
                    warnings.append({
                        "rule": "DATA_TRANSFER_THIRD_PARTY_FORBIDDEN",
                        "event": event.name,
                        "message": "check_third_party_agreement should NOT exist",
                        "recommendation": f"Remove 'check_third_party_agreement' before '{event.name}'. The execution metadata confirms no third-party recipients are involved; checking non-existent legal entities corrupts the semantic integrity of the trace."
                    })

            # =====================================================
            # 2. INTERNATIONAL SAFEGUARD
            # =====================================================

            if international_transfer == "third_country":

                valid_position = any(
                    GDPREnrichmentValidator._is_gdpr_event(e)
                    and e.name == "verify_international_safeguard"
                    and GDPREnrichmentValidator._position(e) == GDPREnrichmentValidator._expected_position("verify_international_safeguard")
                    and e.order < event.order
                    for e in trace.events
                )

                if not valid_position:
                    violations.append({
                        "rule": "DATA_TRANSFER_INTERNATIONAL_REQUIRED",
                        "event": event.name,
                        "message": "Missing verify_international_safeguard BEFORE",
                        "recommendation": f"Inject a 'verify_international_safeguard' validation event BEFORE executing the transfer in '{event.name}'. Cross-border transfers to a third country require validating an adequacy decision, Standard Contractual Clauses (SCCs), or BCRs under GDPR Chapter V."
                    })

            else:

                if has_international_check:
                    warnings.append({
                        "rule": "DATA_TRANSFER_INTERNATIONAL_FORBIDDEN",
                        "event": event.name,
                        "message": "verify_international_safeguard should NOT exist",
                        "recommendation": f"Remove 'verify_international_safeguard' before '{event.name}'. The current data flow stays within European Economic Area (EEA) borders or local nodes, making international screening mechanisms obsolete."
                    })

        return violations, warnings
    


    @staticmethod
    def _automated_decision_rules(trace):

        """
        OCL:
        context Trace

        inv AUTOMATED_DECISION_DISCLOSURE_REQUIRED:
            for all e where e.type = AUTOMATED_DECISION:
                exists g where
                    g.name = automated_logic_disclosure AND
                    g.position = BEFORE AND
                    g.order < e.order
        """

        violations = []
        warnings = []

        for event in trace.events:

            if isinstance(event, GDPREvent):
                continue

            if not event.activity or event.activity.type != ActivityType.AUTOMATED_DECISION:
                continue

            has_disclosure = any(
                isinstance(e, GDPREvent)
                and e.name == "automated_logic_disclosure"
                and e.position == EventPosition.BEFORE
                and e.order < event.order
                for e in trace.events
            )

            if not has_disclosure:
                violations.append({
                    "rule": "AUTOMATED_DECISION_DISCLOSURE_REQUIRED",
                    "event": event.name,
                    "message": "Missing automated_logic_disclosure BEFORE",
                    "recommendation": f"Inject an 'automated_logic_disclosure' information event with position BEFORE the logic execution in '{event.name}'. Under GDPR Art. 13(2)(f) and Art. 22, data subjects have the right to receive meaningful information about the logic involved, as well as the significance and envisaged consequences of automated profiling."
                })

        return violations, warnings
    


    @staticmethod
    def _user_right_request_rules(trace):

        """
        OCL:
        context Trace

        inv USER_RIGHT_REQUEST_RESPONSE_REQUIRED:
            for all e where e.type = USER_RIGHT_REQUEST:
                exists g where
                    g.name = respond_user_right AND
                    g.order > e.order
        """

        violations = []
        warnings = []

        for event in trace.events:

            if GDPREnrichmentValidator._is_gdpr_event(event):
                continue

            if GDPREnrichmentValidator._activity_type(event) != ActivityType.USER_RIGHT_REQUEST:
                continue

            # -------------------------------------------------
            # RULE: respond_user_right AFTER
            # -------------------------------------------------

            has_response = any(
                GDPREnrichmentValidator._is_gdpr_event(e)
                and e.name == "respond_user_right"
                and e.order > event.order
                for e in trace.events
            )

            if not has_response:
                violations.append({
                    "rule": "USER_RIGHT_REQUEST_RESPONSE_REQUIRED",
                    "event": event.name,
                    "message": "Missing respond_user_right AFTER",
                    "recommendation": f"Inject a 'respond_user_right' event with position AFTER '{event.name}'. Under GDPR Art. 12, the controller must provide information on action taken on a request to the data subject without undue delay and at the latest within one month."
                })

            # -------------------------------------------------
            # RULE: verify_request_identity BEFORE
            # -------------------------------------------------

            has_identity = any(
                GDPREnrichmentValidator._is_gdpr_event(e)
                and e.name == "verify_request_identity"
                and e.order < event.order
                for e in trace.events
            )

            if not has_identity:
                violations.append({
                    "rule": "USER_RIGHT_IDENTITY_VERIFICATION",
                    "event": event.name,
                    "message": "Missing verify_request_identity BEFORE",
                    "recommendation": f"Inject a 'verify_request_identity' control step BEFORE executing the request '{event.name}'. GDPR mandates that data controllers use all reasonable measures to verify the identity of a data subject requesting access, ensuring sensitive records are not exposed to malicious third parties."
                })


            # -------------------------------------------------
            # ACCESS RIGHT COMPLIANCE
            # -------------------------------------------------

            if getattr(event, "user_right_type", None) == UserRightType.ACCESS:

                required_events = [
                    "provide_data_copy"
                ]

                missing = []

                for req_event in required_events:

                    exists = any(
                        isinstance(e, GDPREvent)
                        and e.name == req_event
                        and e.order > event.order
                        for e in trace.events
                    )

                    if not exists:
                        missing.append(req_event)

                if missing:
                    violations.append({
                        "rule": "USER_RIGHT_ACCESS_COMPLIANCE",
                        "event": event.name,
                        "message": (
                            "Incomplete access request handling. "
                            f"Missing: {', '.join(missing)}"
                        ),
                        "recommendation": f"Inject the missing events ({', '.join(missing)}) chronologically AFTER '{event.name}'. Under GDPR Art. 15(3), the controller must provide a free, structured copy of the personal data undergoing processing to fulfill the data subject's right of access."
                    })

            # -------------------------------------------------
            # RECTIFICATION COMPLIANCE
            # -------------------------------------------------

            if getattr(event, "user_right_type", None) == UserRightType.RECTIFICATION:

                required_events = [
                    "update_primary_record",
                    "propagate_rectification_to_replicas",
                    "notify_data_rectification_to_recipients",
                    "verify_rectification_consistency"
                ]

                missing = []

                for req_event in required_events:

                    exists = any(
                        isinstance(e, GDPREvent)
                        and e.name == req_event
                        and e.order > event.order
                        for e in trace.events
                    )

                    if not exists:
                        missing.append(req_event)

                if missing:
                    violations.append({
                        "rule": "USER_RIGHT_RECTIFICATION_COMPLIANCE",
                        "event": event.name,
                        "message": (
                            "Incomplete rectification propagation. "
                            f"Missing: {', '.join(missing)}"
                        ),
                        "recommendation": f"Inject the missing engineering pipeline events ({', '.join(missing)}) AFTER '{event.name}'. GDPR Art. 16 requires immediate rectification of inaccurate data, while Art. 19 mandates notifying any third-party recipients about the changes to maintain data consistency."
                    })

            # -------------------------------------------------
            # ERASURE COMPLIANCE
            # -------------------------------------------------

            if getattr(event, "user_right_type", None) == UserRightType.ERASURE:

                required_events = [
                    "erase_primary_record",
                    "propagate_erasure_to_replicas",
                    "notify_third_party_deletion",
                    "verify_erasure_completion"
                ]

                missing = []

                for req_event in required_events:

                    exists = any(
                        isinstance(e, GDPREvent)
                        and e.name == req_event
                        and e.order > event.order
                        for e in trace.events
                    )

                    if not exists:
                        missing.append(req_event)

                if missing:
                    violations.append({
                        "rule": "USER_RIGHT_ERASURE_COMPLIANCE",
                        "event": event.name,
                        "message": (
                            "Incomplete erasure propagation. "
                            f"Missing: {', '.join(missing)}"
                        ),
                        "recommendation": f"Inject the missing cascade deletion events ({', '.join(missing)}) AFTER '{event.name}'. GDPR Art. 17 (Right to Erasure) demands full purge cycles across all active datastores, backups, and downstream processor nodes to prevent orphaned sensitive data."
                    })

                        # -------------------------------------------------
            # RESTRICTION COMPLIANCE
            # -------------------------------------------------

            if getattr(event, "user_right_type", None) == UserRightType.RESTRICTION:

                # -------------------------
                # BEFORE event
                # -------------------------

                has_verify = any(
                    isinstance(e, GDPREvent)
                    and e.name == "verify_restriction_lift_conditions"
                    and e.order < event.order
                    for e in trace.events
                )

                # -------------------------
                # AFTER event
                # -------------------------

                has_mark = any(
                    isinstance(e, GDPREvent)
                    and e.name == "mark_data_as_restricted"
                    and e.order > event.order
                    for e in trace.events
                )

                if not has_verify or not has_mark:

                    missing = []

                    if not has_verify:
                        missing.append("verify_restriction_lift_conditions")

                    if not has_mark:
                        missing.append("mark_data_as_restricted")

                    violations.append({
                        "rule": "USER_RIGHT_RESTRICTION_COMPLIANCE",
                        "event": event.name,
                        "message": (
                            "Incomplete restriction handling. "
                            f"Missing: {', '.join(missing)}"
                        ),
                        "recommendation": f"Ensure 'verify_restriction_lift_conditions' executes BEFORE and 'mark_data_as_restricted' executes AFTER '{event.name}'. GDPR Art. 18 states that restricted data must be explicitly flagged so its active processing is suspended while its accuracy or legal basis is contested."
                    })

            # -------------------------------------------------
            # PORTABILITY COMPLIANCE
            # -------------------------------------------------

            if getattr(event, "user_right_type", None) == UserRightType.PORTABILITY:

                required_events = [
                    "generate_interoperable_format",
                    "transmit_data_to_new_controller"
                ]

                missing = []

                for req_event in required_events:

                    exists = any(
                        isinstance(e, GDPREvent)
                        and e.name == req_event
                        and e.order > event.order
                        for e in trace.events
                    )

                    if not exists:
                        missing.append(req_event)

                # -------------------------
                # ORDER VALIDATION
                # -------------------------

                format_event = next(
                    (
                        e for e in trace.events
                        if isinstance(e, GDPREvent)
                        and e.name == "generate_interoperable_format"
                    ),
                    None
                )

                transmission_event = next(
                    (
                        e for e in trace.events
                        if isinstance(e, GDPREvent)
                        and e.name == "transmit_data_to_new_controller"
                    ),
                    None
                )

                invalid_order = (
                    format_event
                    and transmission_event
                    and transmission_event.order < format_event.order
                )

                if invalid_order:
                    missing.append(
                        "invalid_order(transmit_data_to_new_controller BEFORE generate_interoperable_format)"
                    )

                if missing:
                    violations.append({
                        "rule": "USER_RIGHT_PORTABILITY_COMPLIANCE",
                        "event": event.name,
                        "message": (
                            "Incomplete portability handling. "
                            f"Missing: {', '.join(missing)}"
                        ),
                        "recommendation": f"Fix the workflow topology for '{event.name}'. GDPR Art. 20 mandates that data must be structured in a machine-readable format ('generate_interoperable_format') *strictly before* being securely transmitted to another controller node."
                    })

            # -------------------------------------------------
            # OBJECTION COMPLIANCE
            # -------------------------------------------------

            if getattr(event, "user_right_type", None) == UserRightType.OBJECTION:

                # -------------------------
                # BEFORE event
                # -------------------------

                has_verify = any(
                    isinstance(e, GDPREvent)
                    and e.name == "verify_compelling_legitimate_grounds"
                    and e.order < event.order
                    for e in trace.events
                )

                # -------------------------
                # AFTER event
                # -------------------------

                has_halt = any(
                    isinstance(e, GDPREvent)
                    and e.name == "halt_processing_activities"
                    and e.order > event.order
                    for e in trace.events
                )

                if not has_verify or not has_halt:

                    missing = []

                    if not has_verify:
                        missing.append("verify_compelling_legitimate_grounds")

                    if not has_halt:
                        missing.append("halt_processing_activities")

                    violations.append({
                        "rule": "USER_RIGHT_OBJECTION_COMPLIANCE",
                        "event": event.name,
                        "message": (
                            "Incomplete objection handling. "
                            f"Missing: {', '.join(missing)}"
                        ),
                        "recommendation": f"Inject 'verify_compelling_legitimate_grounds' BEFORE and 'halt_processing_activities' AFTER '{event.name}'. Under GDPR Art. 21, processing must cease instantly unless the controller demonstrates compelling legitimate grounds which override the interests of the data subject."
                    })

            # -------------------------------------------------
            # AUTOMATED DECISION REVIEW COMPLIANCE
            # -------------------------------------------------

            if getattr(event, "user_right_type", None) == UserRightType.AUTOMATED_DECISION_REVIEW:

                required_events = [
                    "contest_automated_decision"
                ]

                missing = []

                for req_event in required_events:

                    exists = any(
                        isinstance(e, GDPREvent)
                        and e.name == req_event
                        and e.order > event.order
                        for e in trace.events
                    )

                    if not exists:
                        missing.append(req_event)

                if missing:
                    violations.append({
                        "rule": "USER_RIGHT_AUTOMATED_DECISION_REVIEW_COMPLIANCE",
                        "event": event.name,
                        "message": (
                            "Incomplete automated decision review handling. "
                            f"Missing: {', '.join(missing)}"
                        ),
                        "recommendation": f"Inject a 'contest_automated_decision' process branch AFTER '{event.name}'. GDPR Art. 22(3) guarantees the data subject the right to obtain human intervention, to express their point of view, and to formally contest the automated systemic decision."
                    })

            # -------------------------------------------------
            # INFORMATION COMPLIANCE
            # -------------------------------------------------

            if getattr(event, "user_right_type", None) == UserRightType.INFORMATION:

                required_events = [
                    "provide_transparency_details"
                ]

                missing = []

                for req_event in required_events:

                    exists = any(
                        isinstance(e, GDPREvent)
                        and e.name == req_event
                        and e.order > event.order
                        for e in trace.events
                    )

                    if not exists:
                        missing.append(req_event)

                if missing:
                    violations.append({
                        "rule": "USER_RIGHT_INFORMATION_COMPLIANCE",
                        "event": event.name,
                        "message": (
                            "Incomplete information request handling. "
                            f"Missing: {', '.join(missing)}"
                        ),
                        "recommendation": f"Inject a 'provide_transparency_details' execution event AFTER '{event.name}'. Pursuant to GDPR Principle of Transparency, controllers must explicitly outline storage periods, processing logic, and data origins when prompted by the data subject."
                    })

        return violations, warnings
    

    @staticmethod
    def _data_deletion_rules(trace):

        """
        OCL:
        context Trace

        inv DATA_DELETION_COMPLIANCE:
            for all e where e.type = DATA_DELETION:
                exists g1 where
                    g1.name = record_retention_period AND
                    g1.order < e.order
                AND
                (
                    exists g2 where g2.name = erase_data
                    OR
                    exists g3 where g3.name = erase_data AND g3.order > e.order
                )
        """

        violations = []
        warnings = []

        for event in trace.events:

            if isinstance(event, GDPREvent):
                continue

            if not event.activity or event.activity.type != ActivityType.DATA_DELETION:
                continue

            # -------------------------
            # retention_period BEFORE
            # -------------------------

            has_retention = any(
                isinstance(e, GDPREvent)
                and e.name == "record_retention_period"
                and e.order < event.order
                for e in trace.events
            )

            if not has_retention:
                violations.append({
                    "rule": "DATA_DELETION_RETENTION_REQUIRED",
                    "event": event.name,
                    "message": "Missing record_retention_period BEFORE",
                    "recommendation": f"Inject a 'record_retention_period' declaration event BEFORE executing the deletion in '{event.name}'. GDPR Art. 5(1)(e) demands that personal data be kept in a form which permits identification for no longer than is necessary; thus, the authorized retention threshold must be verified prior to destruction logs."
                })

            # -------------------------
            # erase_data (RELATED OR AFTER)
            # -------------------------

            has_erase = any(
                isinstance(e, GDPREvent)
                and e.name == "erase_data"
                for e in trace.events
            )

            has_erase_after = any(
                isinstance(e, GDPREvent)
                and e.name == "erase_data"
                and e.order > event.order
                for e in trace.events
            )

            if not has_erase_after:
                violations.append({
                    "rule": "DATA_DELETION_ERASE_REQUIRED",
                    "event": event.name,
                    "message": "Missing erase_data AFTER",
                    "recommendation": f"Inject an 'erase_data' execution event with chronological position AFTER the deletion request marker '{event.name}'. Recording the intent to delete is legally insufficient without executing the technical physical/logical erasure mechanism to meet Accountability metrics."
                })

        return violations, warnings
