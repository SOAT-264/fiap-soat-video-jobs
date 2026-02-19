from video_processor_shared.domain.exceptions import InvalidJobTransitionError
from video_processor_shared.domain.value_objects import JobStatus


def test_start_updates_status_and_started_at(make_job):
    job = make_job()

    job.start()

    assert job.status == JobStatus.PROCESSING
    assert job.started_at is not None


def test_complete_sets_terminal_fields(make_job):
    job = make_job(status=JobStatus.PROCESSING)

    job.complete(frame_count=12, zip_path="outputs/a.zip", zip_size=100)

    assert job.status == JobStatus.COMPLETED
    assert job.frame_count == 12
    assert job.zip_path == "outputs/a.zip"
    assert job.zip_size == 100
    assert job.progress == 100
    assert job.completed_at is not None
    assert job.is_terminal is True


def test_fail_sets_failed_and_error(make_job):
    job = make_job(status=JobStatus.PROCESSING)

    job.fail("boom")

    assert job.status == JobStatus.FAILED
    assert job.error_message == "boom"
    assert job.completed_at is not None


def test_cancel_sets_cancelled(make_job):
    job = make_job(status=JobStatus.PROCESSING)

    job.cancel()

    assert job.status == JobStatus.CANCELLED
    assert job.is_terminal is True


def test_update_progress_out_of_bounds_raises(make_job):
    job = make_job()

    try:
        job.update_progress(101)
        assert False, "Era esperado ValueError"
    except ValueError as exc:
        assert "between 0 and 100" in str(exc)


def test_invalid_transition_raises(make_job):
    job = make_job(status=JobStatus.PENDING)

    try:
        job.complete(frame_count=1, zip_path="x", zip_size=1)
        assert False, "Era esperado InvalidJobTransitionError"
    except InvalidJobTransitionError as exc:
        assert "Cannot transition" in str(exc)


def test_entity_equality_and_hash(make_job):
    job = make_job()
    same_id = make_job(id=job.id)
    other = make_job()

    assert job == same_id
    assert job != other
    assert len({job, same_id, other}) == 2
