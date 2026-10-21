def unique_item_labels(item_ids, labels, taken=()):
    """Map item IDs to their labels, made unique for use as column names or
    JSON keys (#640, #755).

    Some forms use the same label for two items (e.g. a word listed as both a
    noun and a verb). The first keeps the plain label; repeats get _1, _2, ...
    in form order. Labels that are already unique are unchanged.
    """
    used = set(taken)
    unique = {}
    for item_id in item_ids:
        label = labels.get(item_id, item_id)
        candidate, n = label, 0
        while candidate in used:
            n += 1
            candidate = f"{label}_{n}"
        used.add(candidate)
        unique[item_id] = candidate
    return unique
