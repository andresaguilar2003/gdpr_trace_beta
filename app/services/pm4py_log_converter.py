from pm4py.objects.log.obj import EventLog, Trace, Event


def _event_activity_type(event):
    activity_type = getattr(event, "activity_type", None)
    if activity_type is not None:
        return activity_type

    activity = getattr(event, "activity", None)
    return getattr(activity, "type", None) or getattr(activity, "activity_type", None)

def traces_to_pm4py_log(traces, context=None):

    log = EventLog()

    if context:
        log.attributes["gdpr:purpose"] = str(context.purpose)
        log.attributes["gdpr:legal_basis"] = str(context.legal_basis)
        log.attributes["gdpr:data_category"] = str(context.data_category)
        log.attributes["gdpr:data_subject_type"] = str(context.data_subject_type)
        log.attributes["gdpr:processing_operation"] = str(context.processing_operation)
        log.attributes["gdpr:retention_period"] = str(context.retention_period)
        log.attributes["gdpr:processing_domain"] = str(context.processing_domain)
        log.attributes["gdpr:third_party_recipients"] = str(context.has_third_party_recipients)
        log.attributes["gdpr:international_transfer"] = str(context.international_transfer)
        log.attributes["gdpr:transfer_safeguard"] = str(context.transfer_safeguard)
        log.attributes["gdpr:consent_status"] = str(context.consent_status)

    # ------------------------------------

    for t in traces:

        # 🔥 CAMBIO AQUÍ: Validar campo por campo que el valor mutado sea válido 
        # y no sea None ni str(None) antes de pisar los metadatos globales del log
        if hasattr(t, "context") and t.context is not None:
            c = t.context
            
            # Extraemos de forma segura comprobando que el valor interno tenga sustancia
            for attr_name, xml_key in [
                ("legal_basis", "gdpr:legal_basis"),
                ("data_category", "gdpr:data_category"),
                ("retention_period", "gdpr:retention_period"),
                ("has_third_party_recipients", "gdpr:third_party_recipients"),
                ("international_transfer", "gdpr:international_transfer")
            ]:
                val = getattr(c, attr_name, None)
                # Si el atributo del contexto individual tiene un valor real asignado (por las mutaciones)
                if val is not None and str(val).strip().lower() != "none":
                    log.attributes[xml_key] = str(val)

        trace = Trace()
        trace.attributes["concept:name"] = t.trace_id

        for e in t.events:

            event = Event()

            if hasattr(e, "position"):
                # 👉 GDPR EVENT (inyectado)
                event["concept:name"] = e.name

            else:
                # 👉 EVENTO ORIGINAL
                event["concept:name"] = getattr(e, "original_name", e.name)

            # 🔥 NUEVO CAMPO PARA EL GRAFO
            if hasattr(e, "position"):
                # 👉 GDPR event
                event["graph:activity"] = e.name
            else:
                # 👉 evento original
                event["graph:activity"] = _event_activity_type(e) or e.name

            event["time:timestamp"] = e.timestamp

            # 🔥 tipado SIEMPRE separado
            activity_type = _event_activity_type(e)
            if hasattr(activity_type, "name"):
                event["gdpr:activity_type"] = activity_type.name
            else:
                event["gdpr:activity_type"] = str(activity_type)

            if hasattr(e, "user_right_type") and e.user_right_type:
                event["gdpr:user_right_type"] = e.user_right_type.name

            if hasattr(e, "data_fields") and e.data_fields:
                event["gdpr:data_fields"] = ",".join(e.data_fields)

            if hasattr(e, "position") and e.position is not None:
                if hasattr(e.position, "name"):
                    event["gdpr:position"] = e.position.name
                else:
                    event["gdpr:position"] = str(e.position).split(".")[-1].upper()

            trace.append(event)

        log.append(trace)

    return log
