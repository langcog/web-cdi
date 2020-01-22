from researcher_UI.models import InstrumentScore, administration_data, SummaryData, Benchmark
from .models import Instrument_Forms, BackgroundInfo

def calc_benchmark(x1, x2, y1, y2, raw_score):
    if x1 == x2: return int((y1+y2)/2)
    gradient = float(y2-y1)/(x2-x1)
    a = float(y1 - (x1 * gradient))
    return int(a + raw_score * gradient)

def update_summary_scores(administration_instance):
    SummaryData.objects.filter(administration=administration_instance).update(value='')
    
    instrument_scores = InstrumentScore.objects.filter(instrument=administration_instance.study.instrument)
        
    for administration_data_item in administration_data.objects.filter(administration=administration_instance):
        inst = Instrument_Forms.objects.get(instrument=administration_instance.study.instrument, itemID=administration_data_item.item_ID)
        scoring_category = inst.scoring_category if inst.scoring_category else inst.item_type
        
        #this is the scoring 
        for f in InstrumentScore.objects.filter(instrument=administration_instance.study.instrument, category__contains=scoring_category): #items can be counted under multiple Titles check category against all categories
            summary, created = SummaryData.objects.get_or_create(administration=administration_instance, title=f.title)

            if scoring_category in f.category.split(';'):
                if f.kind == "count" :
                    if administration_data_item.value in f.measure.split(';'): #and check all values to see if we increment
                        if summary.value == '': 
                            summary.value = '1'
                        else:
                            summary.value = str(int(summary.value)+1)
                        
                else : 
                    summary.value += administration_data_item.value + '\n'
            
            summary.save()

    #this is the benchmark data
    if Benchmark.objects.filter(instrument=administration_instance.study.instrument).exists():
        try:
            max_age = Benchmark.objects.filter(instrument=administration_instance.study.instrument).order_by('-age')[0].age
            min_age = Benchmark.objects.filter(instrument=administration_instance.study.instrument).order_by('age')[0].age
        except: pass

        try:
            background_info = BackgroundInfo.objects.get(administration=administration_instance)
        except: return
        try:
            age = background_info.age
            if age < min_age: age = min_age
            if age > max_age: age = max_age
        except:
            age=None
        summary, created = SummaryData.objects.get_or_create(administration=administration_instance, title='benchmark age')
        summary.value = str(age)
        summary.save()
        for f in InstrumentScore.objects.filter(instrument=administration_instance.study.instrument):
            if Benchmark.objects.filter(instrument_score=f).exists():
                benchmark = Benchmark.objects.filter(instrument_score=f, age=age)[0]
                if benchmark.percentile == 999:
                    summary, created = SummaryData.objects.get_or_create(administration=administration_instance, title=f.title + ' % yes answers at this age and sex')
                    if background_info.sex == 'M' :
                        summary.value = str(benchmark.raw_score_boy)
                    elif background_info.sex == 'F' :
                        summary.value = str(benchmark.raw_score_girl)
                    summary.save()

                else:
                    summary, created = SummaryData.objects.get_or_create(administration=administration_instance, title=f.title + ' Percentile-sex')
                    benchmarks = Benchmark.objects.filter(instrument_score=f, age=age)
                    unisex_score = sex_score = 0
                    try:
                        raw_score = int(SummaryData.objects.get(administration=administration_instance, title=f.title).value)
                    except:
                        raw_score = 0
                    if background_info.sex == 'M':
                        benchmark = benchmarks[0]
                        sex_score = benchmark.percentile
                        for b in benchmarks[1:]:
                            if b.raw_score_boy <= raw_score: 
                                benchmark = b
                                sex_score = benchmark.percentile
                            else:
                                sex_score = calc_benchmark(benchmark.raw_score_boy, b.raw_score_boy, benchmark.percentile, b.percentile, raw_score)
                                break
                    elif background_info.sex == 'F':
                        benchmark = benchmarks[0]
                        sex_score = benchmark.percentile
                        for b in benchmarks[1:]:
                            if b.raw_score_girl <= raw_score: 
                                benchmark = b
                                sex_score = benchmark.percentile
                            else:
                                sex_score = calc_benchmark(benchmark.raw_score_girl, b.raw_score_girl, benchmark.percentile, b.percentile, raw_score)
                                break
                    
                    if sex_score < 1: sex_score = '<1'
                    summary.value = str(sex_score)
                    summary.save()
                    
                    if not benchmark.raw_score == 9999: 
                        summary, created = SummaryData.objects.get_or_create(administration=administration_instance, title=f.title + ' Percentile-both')
                        unisex_score = benchmark.percentile
                        for b in benchmarks[1:]:
                            if b.raw_score <= raw_score: 
                                benchmark = b
                                unisex_score = benchmark.percentile
                            else:
                                unisex_score = calc_benchmark(benchmark.raw_score, b.raw_score, benchmark.percentile, b.percentile, raw_score)
                                break
                        if unisex_score < 1: unisex_score = '<1'
                        summary.value = str(unisex_score)
                        summary.save()
