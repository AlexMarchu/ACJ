from django.contrib import admin

from contests.models import Contest, ContestSubmission, ContestParticipant, ContestProblem

admin.site.register(Contest)
admin.site.register(ContestSubmission)
admin.site.register(ContestProblem)
admin.site.register(ContestParticipant)
