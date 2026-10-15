from django.db import models


class Translation(models.Model):
    source_language = models.CharField(max_length=10)
    target_language = models.CharField(max_length=10)
    original_text = models.TextField()
    translated_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        preview = self.original_text[:40].replace("\n", " ")
        return f"{self.source_language}->{self.target_language}: {preview}"


class Lesson(models.Model):
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    language = models.CharField(max_length=10, default="es")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (self.title or self.content[:40]).replace("\n", " ")


class Progress(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress")
    user_id = models.CharField(max_length=100, default="local")
    score = models.FloatField(default=0.0)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_id} - {self.lesson.id} - {self.score}"
