# UNRELEASED

* Allow pickling of exceptions and add a test to ensure
  the pickling works as expected. This is needed when error
  classes are pickled by an asynchronous worker (example: celery).
