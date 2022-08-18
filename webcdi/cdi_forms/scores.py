from researcher_UI.models import InstrumentScore, administration_data, SummaryData, Benchmark, Measure
from .models import Instrument_Forms, BackgroundInfo

def calc_benchmark(x1, x2, y1, y2, raw_score):
    if x1 == x2: return int((y1+y2)/2)
    gradient = float(y2-y1)/(x2-x1)
    a = float(y1 - (x1 * gradient))
    return int(a + raw_score * gradient)

def create_benchmark_score(benchmark, age, background_info, administration_instance, f, adjusted):
                if benchmark.percentile == 999:
                    summary, created = SummaryData.objects.get_or_create(administration=administration_instance, title=f.title + f' % yes answers at this age and sex{adjusted}')
                    if background_info.sex == 'M' :
                        summary.value = str(benchmark.raw_score_boy)
                    elif background_info.sex == 'F' :
                        summary.value = str(benchmark.raw_score_girl)
                    summary.save()

                else:
                    summary, created = SummaryData.objects.get_or_create(administration=administration_instance, title=f.title + f'Percentile-sex{adjusted}')
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
                        summary, created = SummaryData.objects.get_or_create(administration=administration_instance, title=f.title + f'Percentile-both{adjusted}')
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
                    if administration_data_item.value in f.scoring_measures.split(';'): #and check all values to see if we increment
                        if summary.value == '': 
                            summary.value = str(Measure.objects.get(instrument_score=f, key=administration_data_item.value).value)
                        else:
                            summary.value = str(int(summary.value)+Measure.objects.get(instrument_score=f, key=administration_data_item.value).value)
                else : 
                    summary.value = administration_data_item.value
            
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

        if age is not None and background_info.early_or_late == 'early':
            try:
                adjusted_benchmark_age = age - int(background_info.due_date_diff / 4)
            except:
                adjusted_benchmark_age = age
        else:
            adjusted_benchmark_age = age
        summary, created = SummaryData.objects.get_or_create(administration=administration_instance, title='adjusted benchmark age')
        summary.value = str(adjusted_benchmark_age)
        summary.save()
        

        for f in InstrumentScore.objects.filter(instrument=administration_instance.study.instrument):
            if Benchmark.objects.filter(instrument_score=f).exists():
                benchmark = Benchmark.objects.filter(instrument_score=f, age=age)[0]
                try:
                    adjusted_benchmark = Benchmark.objects.filter(instrument_score=f, age=adjusted_benchmark_age)[0]
                except:
                    adjusted_benchmark = Benchmark.objects.filter(instrument_score=f).order_by('age')[0]
                create_benchmark_score(benchmark, age, background_info, administration_instance, f, '')
                create_benchmark_score(adjusted_benchmark, adjusted_benchmark_age, background_info, administration_instance, f, ' (adjusted)')
                
                
