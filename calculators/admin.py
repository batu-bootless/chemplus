from django.contrib import admin
from .models import Category, Thread, Answer, AnswerVote, Report

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'author', 'created_at', 'is_deleted')
    list_filter = ('category', 'is_deleted')
    search_fields = ('title', 'content', 'author__username')

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'thread', 'author', 'votes', 'created_at', 'is_deleted')
    list_filter = ('is_deleted',)
    search_fields = ('content', 'author__username')

@admin.register(AnswerVote)
class AnswerVoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'answer', 'user', 'created_at')
    search_fields = ('answer__id', 'user__username')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'item_type', 'item_id', 'reporter', 'reason', 'created_at', 'resolved')
    list_filter = ('item_type', 'resolved')
    search_fields = ('reason', 'reporter__username')
