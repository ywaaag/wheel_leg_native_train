"""Model role registry: source and overall best are distinct from new results."""
CANONICAL_ROLES=('source','latest','best_new','best_overall','accepted')
ROLE_FIELDS={
    'source':'source_baseline','latest':'latest_checkpoint',
    'best_new':'best_new_evaluated_candidate','best_overall':'best_overall_candidate',
    'accepted':'accepted_candidate'}


def is_source(candidate,source_sha256=None):
    return candidate.get('role')=='source' or bool(source_sha256 and candidate.get('checkpoint_sha256')==source_sha256)


def register_roles(selection, *, source,latest,best_new,best_overall,accepted):
    if best_new is not None and is_source(best_new,(source or {}).get('checkpoint_sha256')):
        raise ValueError('source cannot be registered as best_new')
    return {**selection,'source_baseline':source,'latest_checkpoint':latest,
        'best_new_evaluated_candidate':best_new,'best_overall_candidate':best_overall,
        'accepted_candidate':accepted,'model_roles':{
            'source':source,'latest':latest,'best_new':best_new,'best_overall':best_overall,'accepted':accepted},
        'role_semantics':{'source':'frozen baseline; may be overall best or accepted fallback',
            'latest':'last saved checkpoint; can be unevaluated',
            'best_new':'best eligible result produced by this experiment; source excluded',
            'best_overall':'best eligible source or new result under the same protocol',
            'accepted':'eligible accepted model; task-specific acceptance rule retained'}}
