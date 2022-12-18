from researcher_UI.models import InstrumentScore, Benchmark


def get_score_headers(study_obj):
    score_forms = InstrumentScore.objects.filter(instrument=study_obj.instrument)
    score_header = []
    if Benchmark.objects.filter(instrument=study_obj.instrument).exists():
        score_header.append("benchmark age")
    for f in score_forms:  # let's get the scoring headers
        score_header.append(f.title)
        if Benchmark.objects.filter(instrument_score=f).exists():
            benchmark = Benchmark.objects.filter(instrument_score=f)[0]
            if benchmark.percentile == 999:
                score_header.append(f.title + " % yes answers at this age and sex")
            else:
                score_header.append(f.title + " Percentile-sex")
                if not benchmark.raw_score == 9999:
                    score_header.append(f.title + " Percentile-both")
    return score_header
