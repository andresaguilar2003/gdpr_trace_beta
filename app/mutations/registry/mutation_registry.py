from app.mutations.base.mutation_category import (
    MutationCategory
)

from app.mutations.operators.contextual.modify_context_field_mutation import ModifyContextFieldMutation
from app.mutations.operators.structural.remove_event_mutation import (
    RemoveEventMutation
)
from app.mutations.operators.structural.duplicate_event_mutation import (
    DuplicateEventMutation
)

from app.mutations.operators.structural.replace_event_mutation import ReplaceEventMutation
from app.mutations.operators.temporal.swap_event_order_mutation import (
    SwapEventOrderMutation
)
from app.mutations.operators.temporal.wrong_position_mutation import (
    WrongPositionMutation
)

from app.mutations.operators.contextual.modify_data_category_mutation import (
    ModifyDataCategoryMutation
)


def _named(mutation, name):
    mutation.name = name
    return mutation


MUTATION_REGISTRY = {
    "duplicate_legal_basis": {
        "category": MutationCategory.STRUCTURAL,
        "factory": lambda: _named(DuplicateEventMutation("verify_legal_basis"), "duplicate_legal_basis")
    },
    "remove_check_consent": {
        "category": MutationCategory.STRUCTURAL,
        "factory": lambda: RemoveEventMutation("check_consent")
    },
    "replace_encryption_with_retention": {
        "category": MutationCategory.STRUCTURAL,
        "factory": lambda: ReplaceEventMutation("encryption_applied", "retention_period_verify")
    },

    "wrong_position_verify_legal_basis": {
        "category": MutationCategory.TEMPORAL,
        "factory": lambda: _named(WrongPositionMutation("verify_legal_basis"), "wrong_position_verify_legal_basis")
    },
    "swap_identity_verification_and_response": {
        "category": MutationCategory.TEMPORAL,
        "factory": lambda: _named(SwapEventOrderMutation("verify_request_identity", "respond_user_right"), "swap_identity_verification_and_response")
    },

    "change_data_category_to_standard": {
        "category": MutationCategory.CONTEXTUAL,
        "factory": lambda: _named(ModifyDataCategoryMutation("DataCategory.STANDARD"), "change_data_category_to_standard")
    },
    "modify_context_third_party_to_false": {
        "category": MutationCategory.CONTEXTUAL,
        "factory": lambda: _named(ModifyContextFieldMutation("has_third_party_recipients", False), "modify_context_third_party_to_false")
    }
}
