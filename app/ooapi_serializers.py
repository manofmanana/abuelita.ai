"""Simple OOAPI-compatible serializers for lessons/courses.

This is a lightweight mapping to produce interoperable JSON exports.
"""
try:
    from rest_framework import serializers

    class OOAPICourseSerializer(serializers.Serializer):
        id = serializers.CharField()
        title = serializers.CharField()
        description = serializers.CharField()
        languageOfInstruction = serializers.CharField(default="es")
        credits = serializers.FloatField(default=0.5)
        provider = serializers.DictField()

    def export_course_to_ooapi(course):
        serializer = OOAPICourseSerializer({
            "id": f"lesson_{getattr(course, 'id', 'unknown')}",
            "title": getattr(course, 'title', 'Untitled'),
            "description": getattr(course, 'description', ''),
            "languageOfInstruction": getattr(course, 'language', 'es'),
            "credits": getattr(course, 'credits', 0.5),
            "provider": {"name": "Abuelita.ai", "url": "https://abuelita.ai"},
        })
        return serializer.data
except Exception:
    # Fallback simple serializer when DRF isn't installed. Returns plain dict.
    def export_course_to_ooapi(course):
        return {
            "id": f"lesson_{getattr(course, 'id', 'unknown')}",
            "title": getattr(course, 'title', 'Untitled'),
            "description": getattr(course, 'description', ''),
            "languageOfInstruction": getattr(course, 'language', 'es'),
            "credits": getattr(course, 'credits', 0.5),
            "provider": {"name": "Abuelita.ai", "url": "https://abuelita.ai"},
        }
