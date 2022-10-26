END_MESSAGE_CHOICES = [
    ('standard' , 'Standard'),
    ('bespoke', 'Custom'),
    ('combined', 'Combined'),
]

PROLIFIC_SOURCE = 1
CENTIMENT_SOURCE = 2
PARTICIPANT_SOURCE_CHOICES = (
    (0, 'None'),
    (1, 'Prolific'),
    (2, 'Centiment'),
    (3, 'RedCap'),
    (4, 'Lookit'),
    (5, 'Mturk'),
    (6, 'Qualtrics'),
    (99, 'Other')
)