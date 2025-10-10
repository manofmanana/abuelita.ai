"""Safe Moodle bridge for Abuelita.ai.

Uses MOODLE_URL and MOODLE_TOKEN from env. All network errors are logged and
returned as an {'error': ...} dict so callers can handle failures gracefully.
"""
import os
import logging
import requests

logger = logging.getLogger(__name__)

MOODLE_URL = os.getenv("MOODLE_URL")
MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")


def moodle_request(wsfunction, params):
    data = {"wstoken": MOODLE_TOKEN, "wsfunction": wsfunction, "moodlewsrestformat": "json"}
    data.update(params)
    if not MOODLE_URL or not MOODLE_TOKEN:
        logger.warning("Moodle credentials missing; returning error dict")
        return {"error": "Moodle not configured"}
    try:
        r = requests.post(MOODLE_URL, data=data, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error("Moodle API error: %s", e)
        return {"error": str(e)}


def create_course(name):
    return moodle_request("core_course_create_courses", {
        "courses[0][fullname]": name,
        "courses[0][shortname]": name[:20],
        "courses[0][categoryid]": 1,
    })


def create_user(username, email):
    return moodle_request("core_user_create_users", {
        "users[0][username]": username,
        "users[0][email]": email,
        "users[0][password]": "TempPass123!",
    })


def push_lesson_result(user_id, course_id, score):
    return moodle_request("local_abuelita_push_result", {
        "results[0][userid]": user_id,
        "results[0][courseid]": course_id,
        "results[0][score]": score,
    })


def fetch_user_progress(user_id):
    return moodle_request("local_abuelita_get_progress", {"userid": user_id})
