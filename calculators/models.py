from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    def __str__(self):
        return self.name

class Thread(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='threads')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='threads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Answer(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='answers')
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    created_at = models.DateTimeField(auto_now_add=True)
    votes = models.IntegerField(default=0)
    is_deleted = models.BooleanField(default=False)

class AnswerVote(models.Model):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='votes_detail')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('answer', 'user')

class Report(models.Model):
    item_type = models.CharField(max_length=20)
    item_id = models.IntegerField()
    reason = models.CharField(max_length=200)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
