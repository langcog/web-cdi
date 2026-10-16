from whitenoise.storage import CompressedManifestStaticFilesStorage


def _without_source_maps(patterns):
    kept = []
    for extension, rules in patterns:
        rules = tuple(r for r in rules if "sourceMappingURL" not in str(r))
        if rules:
            kept.append((extension, rules))
    return tuple(kept)


class StaticStorage(CompressedManifestStaticFilesStorage):
    """Hashed, compressed static files that ignore source-map comments.

    Vendored libraries (e.g. bootstrap/popper.min.js) reference .map files we
    don't ship; Django's default patterns treat those as missing-file errors.
    CSS url()/@import references are still rewritten and checked.
    """

    patterns = _without_source_maps(CompressedManifestStaticFilesStorage.patterns)
