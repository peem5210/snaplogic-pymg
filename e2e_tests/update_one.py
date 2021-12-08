from e2e_tests.validator import validate_result


def validate_update_one(timing, _, collection_nt, collection_sl):
    undo_func = collection_nt.update_one
    undo_kwargs = {"filter": {"group": 2}, "update": {'$set': {"read": False}}}
    timing = validate_result(timing, undo_func, undo_kwargs, collection_nt.update_one, collection_sl.update_one, filter={"group": 2}, update={'$set': {"read": True}})
    return timing
    # UNDO UPDATE
